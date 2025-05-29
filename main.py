from auth.google_auth import get_service
from config.settings import CORE_HANDLER_SHEET_ID
from datetime import datetime

# Import each pull_* module individually
from services import (
    pull_products,
    pull_sales,
    pull_procurements,
    pull_expenses,
    pull_suppliers,
    pull_resellers,
    pull_investments,
    pull_transactions,
    pull_meetings,
    pull_goals
)

# Map each sheet to the fetch_and_insert function of the corresponding module
PERMISSIONS_MAP = {
    "Products": pull_products.fetch_and_insert,
    "Sales": pull_sales.fetch_and_insert,
    "Procurements": pull_procurements.fetch_and_insert,
    "Expenses": pull_expenses.fetch_and_insert,
    "Suppliers": pull_suppliers.fetch_and_insert,
    "Resellers": pull_resellers.fetch_and_insert,
    "Investments": pull_investments.fetch_and_insert,
    "Cash-Flow": pull_transactions.fetch_and_insert,
    "Business Meetings": pull_meetings.fetch_and_insert,
    "Business Goals": pull_goals.fetch_and_insert
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
            PERMISSIONS_MAP[sheet](sheet, business_id, business_id)

if __name__ == "__main__":
    run()
