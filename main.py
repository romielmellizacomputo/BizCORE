from auth.google_auth import get_service
from config.settings import CORE_HANDLER_SHEET_ID
from datetime import datetime
import services

PERMISSIONS_MAP = {
    "Products": services.pull_products,
    "Sales": services.pull_sales,
    "Procurements": services.pull_procurements,
    "Expenses": services.pull_expenses,
    "Suppliers": services.pull_suppliers,
    "Resellers": services.pull_resellers,
    "Investments": services.pull_investments,
    "Cash-Flow": services.pull_transactions,
    "Business Meetings": services.pull_meetings,
    "Business Goals": services.pull_goals
}

def is_not_expired(expiration_str):
    try:
        exp_date = datetime.strptime(expiration_str, "%a, %b %d, %Y")
        return exp_date > datetime.today()
    except:
        return False

def run():
    service = get_service()
    response = service.spreadsheets().values().get(
        spreadsheetId=CORE_HANDLER_SHEET_ID,
        range="Settings!B3:I"
    ).execute()

    rows = response.get("values", [])

    for row in rows:
        if len(row) < 8:
            continue
        business_id, permissions, expiry = row[0], row[5], row[7]
        if not is_not_expired(expiry):
            continue
        permission_list = [perm.strip().lower() for perm in permissions.split(",")]
        sheets_to_process = (
            PERMISSIONS_MAP.keys() if "all" in permission_list else
            [s for s in PERMISSIONS_MAP if s.lower() in permission_list]
        )
        for sheet in sheets_to_process:
            PERMISSIONS_MAP[sheet].fetch_and_insert(sheet, business_id, business_id)

if __name__ == "__main__":
    run()
