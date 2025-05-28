from auth.google_auth import get_sheets_service
from config.settings import CORE_SHEET_ID, START_ROW

def fetch_meetings(child_id):
    service = get_sheets_service()
    sheet = service.spreadsheets()
    range_name = f'Business Meetings!B{START_ROW}:N'
    result = sheet.values().get(spreadsheetId=CORE_SHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    filtered = []
    for row in values:
        if len(row) > 3 and row[3] == child_id:
            filtered.append(row)
    return filtered
