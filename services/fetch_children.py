from auth.google_auth import get_sheets_service
from config.settings import CORE_HANDLER_SHEET_ID
from utils.formatter import is_not_expired, parse_permissions

def fetch_active_children():
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Read the range Settings!B3:I (columns B to I)
    # B = children IDs, G = permissions, H = unknown, I = expiration dates
    # B=2, I=9 (1-indexed in A1 notation: B3:I)
    result = sheet.values().get(spreadsheetId=CORE_HANDLER_SHEET_ID,
                                range='Settings!B3:I').execute()
    values = result.get('values', [])

    active_children = []
    for row in values:
        # Defensive access - row might have fewer columns
        child_id = row[0] if len(row) > 0 else None
        permissions = row[5] if len(row) > 5 else ''
        expiration = row[7] if len(row) > 7 else ''

        if not child_id:
            continue
        if not is_not_expired(expiration):
            continue
        perms = parse_permissions(permissions)
        if not perms:
            continue

        active_children.append({
            'child_id': child_id,
            'permissions': perms
        })

    return active_children
