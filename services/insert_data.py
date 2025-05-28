from auth.google_auth import get_sheets_service

def clear_and_insert(sheet_id, sheet_name, start_row, col_start, col_end, data):
    """
    Clears target range and inserts data starting at (start_row, col_start).
    Columns: col_start to col_end (letters)
    """
    service = get_sheets_service()
    sheets = service.spreadsheets()

    # Clear existing data
    clear_range = f'{sheet_name}!{col_start}{start_row}:{col_end}'
    sheets.values().clear(spreadsheetId=sheet_id, range=clear_range).execute()

    # Insert new data starting at start_row col_start
    insert_range = f'{sheet_name}!{col_start}{start_row}'
    sheets.values().update(
        spreadsheetId=sheet_id,
        range=insert_range,
        valueInputOption='RAW',
        body={'values': data}
    ).execute()
