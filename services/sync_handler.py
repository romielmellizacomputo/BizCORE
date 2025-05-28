# File: services/sync_handler.py
import datetime
from auth.google_auth import get_google_sheets_service
from config.settings import CORE_HANDLER_ID, PERMISSIONS_SHEET_MAP


def get_valid_child_sheets():
    sheet = get_google_sheets_service()
    result = sheet.values().get(spreadsheetId=CORE_HANDLER_ID, range="Settings!B3:I").execute()
    values = result.get('values', [])

    today = datetime.datetime.today().date()
    valid_children = []

    for row in values:
        try:
            child_id = row[0] if len(row) > 0 else None
            permissions = row[6].split(",") if len(row) > 6 else []
            expiry = datetime.datetime.strptime(row[7], "%a, %b %d, %Y").date() if len(row) > 7 else None

            if child_id and permissions and expiry and expiry >= today:
                valid_children.append({
                    "child_id": child_id.strip(),
                    "permissions": [p.strip() for p in permissions]
                })
        except Exception as e:
            continue

    return valid_children
