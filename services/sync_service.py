# --- services/sync_service.py ---
from datetime import datetime
from auth.google_auth import get_gspread_client
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP, ALL_PERMISSIONS

import re

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%a, %b %d, %Y")
    except:
        return None

def get_valid_business_ids(sheet):
    records = sheet.worksheet("Settings").get_all_values()
    today = datetime.today().date()
    ids_permissions = []

    for row in records[2:]:  # skip headers
        if len(row) >= 9:
            biz_id = row[1]
            permissions = re.split(r",\s*", row[6]) if row[6] else []
            expiry = parse_date(row[8])

            if expiry and expiry.date() >= today and permissions:
                ids_permissions.append((biz_id, permissions))
    return ids_permissions

def fetch_data(sheet, worksheet_name, business_id, col_start, col_end):
    worksheet = sheet.worksheet(worksheet_name)
    all_data = worksheet.get_all_values()[3:]  # skip to row 4
    result = []

    start_col_idx = ord(col_start) - ord("A")
    end_col_idx = ord(col_end) - ord("A") + 1

    for row in all_data:
        if len(row) > 3 and row[3] == business_id:
            row_key = row[1] if len(row) > 1 else ""
            row_data = row[start_col_idx:end_col_idx]
            result.append([row_key] + row_data)

    return result

def clear_and_insert(target_ws, start_col, data):
    start_col_idx = ord(start_col) - ord("A")
    end_col_idx = start_col_idx + max(len(row) for row in data) if data else start_col_idx
    range_to_clear = f"{start_col}11:{chr(ord('A') + end_col_idx - 1)}"
    target_ws.batch_clear([range_to_clear])

    for i, row in enumerate(data):
        cell_list = target_ws.range(f"{start_col}{11+i}:{chr(ord(start_col)+len(row)-1)}{11+i}")
        for j, cell in enumerate(cell_list):
            cell.value = row[j]
        target_ws.update_cells(cell_list)

def run_sync():
    client = get_gspread_client()
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)
    core = client.open_by_key(CORE_SHEET_ID)

    ids_permissions = get_valid_business_ids(core_handler)

    for biz_id, permissions in ids_permissions:
        perms = ALL_PERMISSIONS if any(p.lower() == "all" for p in permissions) else permissions
        for perm in perms:
            if perm not in PERMISSION_SHEET_MAP:
                continue
            sheet_name, col_start, col_end = PERMISSION_SHEET_MAP[perm]
            data = fetch_data(core, sheet_name, biz_id, col_start, col_end)
            if not data:
                continue

            try:
                target_sheet = client.open_by_key(biz_id)
                target_ws = target_sheet.worksheet(sheet_name)
                clear_and_insert(target_ws, "G", data)
            except Exception as e:
                print(f"Error inserting into {sheet_name} for {biz_id}: {e}")
