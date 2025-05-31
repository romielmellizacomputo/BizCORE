# --- services/sync_to_handler.py ---
from datetime import datetime
import os

from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP
from googleapiclient.discovery import build
from utils.logger import write_log_to_sheet


def fetch_business_sheets(core):
    """Returns a list of (worksheet, business_name) from the CORE workbook."""
    business_sheets = []
    for ws in core.worksheets():
        try:
            company_name = ws.acell("C4").value
            if company_name:
                business_sheets.append((ws, company_name))
        except Exception:
            continue
    return business_sheets


def fetch_data_from_ws(ws, col_start, col_end):
    all_data = ws.get_all_values()[3:]  # start from row 4
    result = []

    start_col_idx = ord(col_start) - ord("A")
    end_col_idx = ord(col_end) - ord("A") + 1

    for row in all_data:
        if len(row) > 1 and row[1]:  # ensure key column exists
            row_key = row[1]
            row_data = row[start_col_idx:end_col_idx]
            result.append([row_key] + row_data)

    return result


def clear_only_values(sheet_id, range_str, creds):
    service = build('sheets', 'v4', credentials=creds)
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=range_str,
        body={}
    ).execute()


def insert_data_preserving_format(sheet_id, start_cell, data, creds):
    service = build('sheets', 'v4', credentials=creds)
    body = {
        'range': start_cell,
        'majorDimension': 'ROWS',
        'values': data
    }
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=start_cell,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()


def add_notes_to_column(sheet_id, sheet_name, start_row, num_notes, note_text, creds):
    """Add note_text to G-column cells (G11 and downward)"""
    service = build('sheets', 'v4', credentials=creds)

    requests = []
    start_row_index = start_row - 1  # API uses 0-based index

    for i in range(num_notes):
        requests.append({
            "updateCells": {
                "range": {
                    "sheetId": get_sheet_id_by_name(sheet_id, sheet_name, creds),
                    "startRowIndex": start_row_index + i,
                    "endRowIndex": start_row_index + i + 1,
                    "startColumnIndex": 6,  # Column G
                    "endColumnIndex": 7
                },
                "rows": [{
                    "values": [{
                        "note": note_text
                    }]
                }],
                "fields": "note"
            }
        })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()


def get_sheet_id_by_name(sheet_id, sheet_name, creds):
    """Helper to get sheet ID from name."""
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise ValueError(f"Sheet {sheet_name} not found")


def run_sync_to_handler():
    client, raw_creds = get_gspread_and_raw_creds()
    core = client.open_by_key(CORE_SHEET_ID)
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)

    business_sheets = fetch_business_sheets(core)

    for ws, company_name in business_sheets:
        sheet_name = ws.title

        if sheet_name not in [info[0] for info in PERMISSION_SHEET_MAP.values()]:
            continue

        # Find mapping for this sheet
        for perm, (perm_sheet_name, col_start, col_end) in PERMISSION_SHEET_MAP.items():
            if perm_sheet_name == sheet_name:
                data = fetch_data_from_ws(ws, col_start, col_end)
                if not data:
                    continue

                try:
                    target_ws = core_handler.worksheet(sheet_name)

                    num_cols = max(len(row) for row in data)
                    start_col_idx = ord("G")
                    end_col_letter = chr(start_col_idx + num_cols - 1)
                    range_to_clear = f"G11:{end_col_letter}"

                    # Clear values only
                    clear_only_values(CORE_HANDLER_SHEET_ID, f"{sheet_name}!{range_to_clear}", raw_creds)

                    # Insert values
                    insert_data_preserving_format(
                        CORE_HANDLER_SHEET_ID,
                        f"{sheet_name}!G11",
                        data,
                        raw_creds
                    )

                    # Add notes on column G with the company name
                    add_notes_to_column(
                        CORE_HANDLER_SHEET_ID,
                        sheet_name,
                        start_row=11,
                        num_notes=len(data),
                        note_text=company_name,
                        creds=raw_creds
                    )

                    write_log_to_sheet(CORE_HANDLER_SHEET_ID, sheet_name, raw_creds)

                except Exception as e:
                    print(f"Error syncing {sheet_name} for {company_name}: {e}")
                break


def run_sync():
    run_sync_to_handler()
