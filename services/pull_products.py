from auth.google_auth import get_sheets_service
from config.settings import CORE_SHEET_ID, START_ROW

def fetch_products(child_id):
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Read Products sheet columns B to U (B + G:U)
    # We want rows where column D == child_id, data from row 4 down
    # We'll read from B4:U (all rows starting row 4)

    range_name = f'Products!B{START_ROW}:U'
    result = sheet.values().get(spreadsheetId=CORE_SHEET_ID, range=range_name).execute()
    values = result.get('values', [])

    filtered = []
    for row in values:
        # Ensure the row has enough columns, check D column (index 3)
        if len(row) > 3 and row[3] == child_id:
            filtered.append(row)
    return filtered
