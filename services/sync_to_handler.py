# --- sync_to_handler.py ---

from datetime import datetime
import re

from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP, ALL_PERMISSIONS
from googleapiclient.discovery import build
from utils.logger import write_log_to_sheet


def fetch_all_data(sheet, worksheet_name, col_start, col_end):
    """
    Fetch all data starting from row 4 (index 3), all rows, between col_start and col_end.
    """
    worksheet = sheet.worksheet(worksheet_name)
    all_data = worksheet.get_all_values()[3:]  # skip first 3 rows (header)
    start_col_idx = ord(col_start) - ord("A")
    end_col_idx = ord(col_end) - ord("A") + 1

    result = []
    for row in all_data:
        row_data = row[start_col_idx:end_col_idx]
        result.append(row_data)
    return result


def fetch_business_names(sheet):
    """
    Fetch business/company names from CORE sheet column C starting from row 4.
    """
    worksheet = sheet.worksheet("Settings")  # assuming business names are in a 'Settings' or main sheet
    # Or fetch from the main sheet if specified
    # For flexibility, let's assume business names are in 'Businesses' sheet or 'CORE' main sheet:

    # Let's try main sheet, assuming business names in C4:C (index 3 onward)
    worksheet = sheet.get_worksheet(0)  # first sheet
    names = worksheet.col_values(3)[3:]  # col C index=3, skip first 3 rows
    return names


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


def add_notes_to_cells(sheet_id, sheet_name, notes_range, notes, creds):
    """
    Add notes (comments) to cells in the notes_range with given notes list.

    notes_range: e.g. 'G11:G100'
    notes: list of strings, one per cell in the range
    """
    service = build('sheets', 'v4', credentials=creds)

    # Convert A1 notation range to grid range
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = spreadsheet['sheets']
    sheet_id_int = None
    for s in sheets:
        if s['properties']['title'] == sheet_name:
            sheet_id_int = s['properties']['sheetId']
            break
    if sheet_id_int is None:
        raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet {sheet_id}")

    # Parse notes_range like G11:Gxxx
    # Assume single column
    import re
    m = re.match(r'([A-Z]+)(\d+):([A-Z]+)(\d+)', notes_range)
    if not m:
        raise ValueError(f"Invalid range: {notes_range}")

    start_col, start_row, end_col, end_row = m.groups()
    start_row = int(start_row) - 1  # zero-indexed
    end_row = int(end_row) - 1

    # Build requests for batchUpdate
    requests = []
    for i, note in enumerate(notes):
        requests.append({
            "updateCells": {
                "range": {
                    "sheetId": sheet_id_int,
                    "startRowIndex": start_row + i,
                    "endRowIndex": start_row + i + 1,
                    "startColumnIndex": ord(start_col) - ord('A'),
                    "endColumnIndex": ord(start_col) - ord('A') + 1,
                },
                "rows": [{
                    "values": [{
                        "note": note
                    }]
                }],
                "fields": "note"
            }
        })

    body = {
        "requests": requests
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body=body
    ).execute()


def run_sync():
    client, raw_creds = get_gspread_and_raw_creds()
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)
    core = client.open_by_key(CORE_SHEET_ID)

    # Fetch all business names from CORE sheet (column C, row 4+)
    business_names = fetch_business_names(core)

    # We assume business_names align with rows in data, i.e. first data row in sheets corresponds to business_names[0], etc.
    # For each permission, fetch all data from CORE and insert into CORE_HANDLER.
    for perm in ALL_PERMISSIONS:
        if perm not in PERMISSION_SHEET_MAP:
            continue

        sheet_name, col_start, col_end = PERMISSION_SHEET_MAP[perm]

        data = fetch_all_data(core, sheet_name, col_start, col_end)
        if not data:
            continue

        # Insert data into CORE_HANDLER starting at G11 (same place)
        # Prepare the note comments to add business name per row at G column cells
        # Length of data rows might be more than business_names - handle gracefully

        # Clear range G11:... depending on data width and length
        num_cols = max(len(row) for row in data)
        num_rows = len(data)
        start_col_idx = ord("G")
        end_col_letter = chr(start_col_idx + num_cols - 1)
        end_row = 11 + num_rows - 1
        range_to_clear = f"{sheet_name}!G11:{end_col_letter}{end_row}"

        # Clear values only (keep formatting)
        clear_only_values(CORE_HANDLER_SHEET_ID, range_to_clear, raw_creds)

        # Insert data
        insert_data_preserving_format(
            CORE_HANDLER_SHEET_ID,
            f"{sheet_name}!G11",
            data,
            raw_creds
        )

        # Add notes to G11:G?? with company names
        notes_range = f"G11:G{end_row}"
        # Use business_names for notes - fallback empty string if out of range
        notes = []
        for i in range(num_rows):
            note = business_names[i] if i < len(business_names) else ""
            notes.append(note)

        add_notes_to_cells(CORE_HANDLER_SHEET_ID, sheet_name, notes_range, notes, raw_creds)

        # Log the sync
        write_log_to_sheet(CORE_HANDLER_SHEET_ID, sheet_name, raw_creds)


if __name__ == "__main__":
    run_sync()
