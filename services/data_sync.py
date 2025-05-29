import json
import os
import gspread
from google.oauth2.service_account import Credentials

# Load credentials from GitHub secrets
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('BIZNEST_AGENT'))
CORE_SHEET_ID = os.getenv('CORE')

# Sheet metadata
SHEET_RANGES = {
    "Products": ("H10", "P10"),
    "Sales": ("H10", "P10"),
    "Procurements": ("H10", "S10"),
    "Expenses": ("H10", "S10"),
    "Suppliers": ("H10", "R10"),
    "Resellers": ("H10", "P10"),
    "Investments": ("H10", "Q10"),
    "Cash-Flow": ("H10", "M10"),
    "Business Meetings": ("H10", "O10"),
    "Business Goals": ("H10", "O10")
}

def get_gc():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
    return gspread.authorize(creds)

def fetch_sheet_data(sheet_id, sheet_name):
    gc = get_gc()
    source_sheet = gc.open_by_key(sheet_id)
    sheet = source_sheet.worksheet(sheet_name)
    dashboard = source_sheet.worksheet("Dashboard")

    # Fetch metadata
    h3 = dashboard.acell("H3").value or ""
    h5 = dashboard.acell("H5").value or ""
    m5 = dashboard.acell("M5").value or ""

    # Get data range
    if sheet_name not in SHEET_RANGES:
        raise ValueError(f"No defined range for {sheet_name}")
    start_col, end_col = SHEET_RANGES[sheet_name]
    data_range = f"{start_col}10:{end_col}"
    data = sheet.get(data_range)

    # Show log
    sheet.update_acell("H3", "Processing...")

    return h3, h5, m5, data, sheet

def fetch_core_data():
    gc = get_gc()
    return gc.open_by_key(CORE_SHEET_ID)

def generate_unique_reference(core, sheet_name):
    import uuid
    base = "SEPA"
    while True:
        ref = f"{base}-{uuid.uuid4().hex[:8].upper()}"
        for worksheet in core.worksheets():
            existing_refs = worksheet.col_values(2)
            if ref not in existing_refs:
                return ref

def insert_or_update_data(core, sheet_name, h3, h5, m5, data_rows, sheet_id):
    target = core.worksheet(sheet_name)
    core_refs = target.col_values(2)
    start_row = 4  # B4 is the beginning
    logs = []

    for idx, row in enumerate(data_rows):
        g_value = row[0] if row else None  # G10 holds Reference No.
        data_to_insert = [None, h3, sheet_id, m5, h5] + row

        if g_value:
            # Update path
            if g_value in core_refs:
                row_index = core_refs.index(g_value) + 1
                target.update(f"B{row_index}:Z{row_index}", [data_to_insert[1:]])
                logs.append(f"Updated: {g_value}")
            else:
                logs.append(f"Skip update (ref not found): {g_value}")
        else:
            # Insert new
            ref = generate_unique_reference(core, sheet_name)
            data_to_insert[0] = ref
            insert_range = f"B{start_row + idx}:Z{start_row + idx}"
            target.update(insert_range, [data_to_insert])
            logs.append(f"Inserted: {ref}")

    return logs

def write_log(sheet, message):
    sheet.update_acell("H3", message)

def main(sheet_id, sheet_name):
    try:
        h3, h5, m5, data_rows, sheet = fetch_sheet_data(sheet_id, sheet_name)
        core = fetch_core_data()
        logs = insert_or_update_data(core, sheet_name, h3, h5, m5, data_rows, sheet_id)
        for log in logs:
            write_log(sheet, log)
    except Exception as e:
        write_log(sheet, f"Error: {str(e)}")
        raise
