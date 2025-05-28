# File: services/sync_core.py
from config.settings import CORE_SHEET_ID, PERMISSIONS_SHEET_MAP
from auth.google_auth import get_google_sheets_service


FETCH_RANGES = {
    "Products": ("G4:U", "V"),
    "Sales": ("G4:T", "U"),
    "Procurements": ("G4:V", "W"),
    "Expenses": ("G4:T", "U"),
    "Suppliers": ("G4:R", "S"),
    "Resellers": ("G4:R", "S"),
    "Investments": ("G4:S", "T"),
    "Cash-Flow": ("G4:N", "O"),
    "Business Meetings": ("G4:N", "O"),
    "Business Goals": ("G4:N", "O")
}


def fetch_core_data(sheet_name, child_id):
    sheet = get_google_sheets_service()
    result = sheet.values().get(spreadsheetId=CORE_SHEET_ID, range=f"{sheet_name}!B4:{FETCH_RANGES[sheet_name][0][-1]}").execute()
    rows = result.get("values", [])

    matching = []
    for row in rows:
        if len(row) >= 3 and row[2].strip() == child_id:
            b_value = row[0] if len(row) > 0 else ""
            data = row[5:] if len(row) >= 6 else []
            matching.append([*data, b_value])

    return matching


def update_child_sheet(child_id, sheet_name, values):
    sheet = get_google_sheets_service()
    data_range = FETCH_RANGES[sheet_name][0].replace("4", "11")

    # Clear first
    sheet.values().clear(spreadsheetId=child_id, range=f"{sheet_name}!{data_range}").execute()

    # Update next
    sheet.values().update(
        spreadsheetId=child_id,
        range=f"{sheet_name}!{data_range}",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()
