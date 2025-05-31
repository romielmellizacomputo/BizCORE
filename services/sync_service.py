# --- services/sync_service.py ---
from datetime import datetime
import re
import os

from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP, ALL_PERMISSIONS
from googleapiclient.discovery import build
from utils.logger import write_log_to_sheet


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


def clear_only_values(sheet_id, range_str, creds):
    service = build('sheets', 'v4', credentials=creds)
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=range_str,
        body={}
    ).execute()


def insert_data_preserving_format(sheet_id, start_cell, data, creds):
    service = build('sheets', 'v4', credentials=creds)
    body = {
        'range': start_cell,
        'majorDimension': 'ROWS',
        'values': data
    }
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=start_cell,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()


def run_sync():
    client, raw_creds = get_gspread_and_raw_creds()
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)
    core = client.open_by_key(CORE_SHEET_ID)

    ids_permissions = get_valid_business_ids(core_handler)

    for biz_id, permissions in ids_permissions:
        perms = ALL_PERMISSIONS if any(p.lower() == "all" for p in permissions) else permissions

        for perm in perms:
            if perm not in PERMISSION_SHEET_MAP:
                continue

            sheet_name, col_start, col_end = PERMISSION_SHEET_MAP[perm]

            # Add retry mechanism with exponential backoff
            for attempt in range(5):  # max 5 attempts
                try:
                    data = fetch_data(core, sheet_name, biz_id, col_start, col_end)
                    break  # success
                except APIError as e:
                    if "Quota exceeded" in str(e) and attempt < 4:
                        sleep_time = 2 ** attempt + random.uniform(0, 1)
                        print(f"[Retry {attempt+1}] Quota hit. Sleeping for {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                    else:
                        print(f"Error fetching data for {biz_id} in {sheet_name}: {e}")
                        data = []
                        break

            if not data:
                continue

            try:
                target_sheet = client.open_by_key(biz_id)
                target_ws = target_sheet.worksheet(sheet_name)

                num_cols = max(len(row) for row in data)
                start_col_idx = ord("G")
                end_col_letter = chr(start_col_idx + num_cols - 1)
                range_to_clear = f"G11:{end_col_letter}"

                clear_only_values(biz_id, f"{sheet_name}!{range_to_clear}", raw_creds)
                insert_data_preserving_format(
                    biz_id,
                    f"{sheet_name}!G11",
                    data,
                    raw_creds
                )
                write_log_to_sheet(biz_id, sheet_name, raw_creds)

                # Add a short delay between full operations
                time.sleep(1.2)  # reduce this as needed

            except Exception as e:
                print(f"Error inserting into {sheet_name} for {biz_id}: {e}")

