# --- services/sync_to_handler.py ---

from datetime import datetime
import os

from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP
from googleapiclient.discovery import build


def fetch_business_names(core_sheet):
    # Just fetch all business names from CORE sheet column C starting from row 4
    # Assuming the main business list is in the first worksheet
    ws = core_sheet.get_worksheet(0)  # first sheet
    business_names = ws.col_values(3)[3:]  # C column, zero-indexed row 3 means start at row 4 (indexing from 0)
    # Filter out empty names
    return [name for name in business_names if name.strip()]


def fetch_all_data(core_sheet, sheet_name, col_start, col_end):
    ws = core_sheet.worksheet(sheet_name)
    all_data = ws.get_all_values()[3:]  # skip first 3 rows (header rows)
    
    start_col_idx = ord(col_start) - ord("A")
    end_col_idx = ord(col_end) - ord("A") + 1

    data = []
    for row in all_data:
        # get slice for desired columns; pad row if short
        slice_row = row[start_col_idx:end_col_idx] if len(row) >= end_col_idx else row[start_col_idx:] + [""]*(end_col_idx - len(row))
        data.append(slice_row)
    return data


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


def add_notes_to_cells(sheet_id, sheet_name, start_row, col_letter, notes, creds):
    """
    Add notes to cells in column col_letter, starting at start_row, 
    with each note corresponding to each row.
    """
    service = build('sheets', 'v4', credentials=creds)

    requests = []
    for i, note in enumerate(notes):
        requests.append({
            "updateCells": {
                "rows": [{
                    "values": [{
                        "note": note
                    }]
                }],
                "fields": "note",
                "range": {
                    "sheetId": get_sheet_id(service, sheet_id, sheet_name),
                    "startRowIndex": start_row - 1 + i,
                    "endRowIndex": start_row + i,
                    "startColumnIndex": ord(col_letter) - ord('A'),
                    "endColumnIndex": ord(col_letter) - ord('A') + 1
                }
            }
        })

    if requests:
        body = {"requests": requests}
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()


def get_sheet_id(service, spreadsheet_id, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise Exception(f"Sheet {sheet_name} not found")


def run_sync():
    client, raw_creds = get_gspread_and_raw_creds()
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)
    core = client.open_by_key(CORE_SHEET_ID)

    business_names = fetch_business_names(core)  # List of company names from CORE C4:C

    for perm, (sheet_name, col_start, col_end) in PERMISSION_SHEET_MAP.items():
        # Fetch all data from CORE for this sheet
        data = fetch_all_data(core, sheet_name, col_start, col_end)
        if not data:
            continue

        try:
            handler_ws = core_handler.worksheet(sheet_name)

            # Calculate end column letter for clearing
            num_cols = max(len(row) for row in data)
            start_col_idx = ord("G")
            end_col_letter = chr(start_col_idx + num_cols - 1)
            range_to_clear = f"G11:{end_col_letter}"

            # Clear only values preserving formatting
            clear_only_values(CORE_HANDLER_SHEET_ID, f"{sheet_name}!{range_to_clear}", raw_creds)

            # Insert data starting at G11
            insert_data_preserving_format(CORE_HANDLER_SHEET_ID, f"{sheet_name}!G11", data, raw_creds)

            # Add company name as note on column G starting at row 11, one note per row
            # If data rows and business_names rows mismatch, repeat or truncate as needed:
            notes = business_names[:len(data)]
            # If not enough business names, fill with empty string
            if len(notes) < len(data):
                notes.extend([""] * (len(data) - len(notes)))

            add_notes_to_cells(CORE_HANDLER_SHEET_ID, sheet_name, start_row=11, col_letter='G', notes=notes, creds=raw_creds)

        except Exception as e:
            print(f"Error syncing sheet {sheet_name} to CORE_HANDLER: {e}")

