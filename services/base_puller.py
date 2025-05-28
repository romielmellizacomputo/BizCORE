# ============================
# services/base_puller.py (new file for shared logic)
# ============================
from auth.google_auth import get_gspread_client
from config.settings import CORE_ID, CORE_HANDLER_ID, SHEET_MAPPINGS
from utils.formatter import is_not_expired

def get_children_to_update():
    client = get_gspread_client()
    handler_sheet = client.open_by_key(CORE_HANDLER_ID).worksheet("Settings")
    ids = handler_sheet.col_values(2)[2:]  # B3:B
    permissions = handler_sheet.col_values(7)[2:]  # G3:G
    expiries = handler_sheet.col_values(8)[2:]  # H3:H

    today_children = []
    for i, (child_id, perms, expiry) in enumerate(zip(ids, permissions, expiries)):
        if is_not_expired(expiry):
            perm_list = [p.strip() for p in perms.split(",") if p.strip()]
            if any(p in SHEET_MAPPINGS or p.lower() == "all" for p in perm_list):
                today_children.append({"sheet_id": child_id, "permissions": perm_list})

    return today_children

def fetch_and_push_data(sheet_name):
    client = get_gspread_client()
    core_sheet = client.open_by_key(CORE_ID).worksheet(sheet_name)

    start_col, end_col = SHEET_MAPPINGS[sheet_name]
    range_str = f"{start_col}4:{end_col}"
    values = core_sheet.get(range_str)
    ids = core_sheet.col_values(4)[3:]  # D4:D
    bs = core_sheet.col_values(2)[3:]   # B4:B

    children = get_children_to_update()

    for child in children:
        child_id = child['sheet_id']
        perms = child['permissions']

        if sheet_name in perms or "ALL" in perms or "All" in perms:
            matched_rows = [row for i, row in enumerate(values) if ids[i] == child_id]
            b_values = [b for i, b in enumerate(bs) if ids[i] == child_id]

            if not matched_rows:
                continue

            child_sheet = client.open_by_key(child_id).worksheet(sheet_name)
            clear_range = f"{start_col}11:{end_col}"
            child_sheet.batch_clear([clear_range])

            # Prepare combined rows with B + G-U
            data_to_insert = []
            for i, row in enumerate(matched_rows):
                padded = row + [""] * (ord(end_col) - ord(start_col) + 1 - len(row))
                data_to_insert.append([b_values[i]] + padded)

            insert_range = f"{chr(ord(start_col)-1)}11"
            child_sheet.update(insert_range, data_to_insert)
