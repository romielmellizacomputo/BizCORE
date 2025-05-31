# --- services/sync_service.py ---
import time
import random
import os
import re
from datetime import datetime

import gspread
from gspread.exceptions import APIError
from googleapiclient.discovery import build

from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID, PERMISSION_SHEET_MAP, ALL_PERMISSIONS
from utils.logger import write_log_to_sheet


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%a, %b %d, %Y")
    except:
        return None


def retry_with_backoff(retries=5, backoff_in_seconds=1, allowed_errors=(Exception,)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = backoff_in_seconds
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except allowed_errors as e:
                    if attempt == retries - 1:
                        raise
                    print(f"[Retrying] {func.__name__} failed with: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay + random.uniform(0, 0.5))  # Add jitter
                    delay *= 2
        return wrapper
    return decorator


@retry_with_backoff(allowed_errors=(APIError,))
def get_valid_business_ids(sheet):
    records = sheet.worksheet("Settings").get_all_values()
    today = datetime.today().date()
    ids_permissions = []

    for row in records[2:]:  # Skip headers
        if len(row) >= 9:
            biz_id = row[1]
            permissions = re.split(r",\s*", row[6]) if row[6] else []
            expiry = parse_date(row[8])

            if expiry and expiry.date() >= today and permissions:
                ids_permissions.append((biz_id, permissions))
    return ids_permissions


@retry_with_backoff(allowed_errors=(APIError,))
def fetch_data(sheet, worksheet_name, business_id, col_start, col_end):
    worksheet = sheet.worksheet(worksheet_name)
    all_data = worksheet.get_all_values()[3:]  # Skip to row 4
    result = []

    start_col_idx = ord(col_start) - ord("A")
    end_col_idx = ord(col_end) - ord("A") + 1

    for row in all_data:
        if len(row) > 3 and row[3] == business_id:
            row_key = row[1] if len(row) > 1 else ""
            row_data = row[start_col_idx:end_col_idx]
            result.append([row_key] + row_data)

    return result


@retry_with_backoff(allowed_errors=(APIError,))
def clear_only_values_with_service(service, sheet_id, range_str):
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=range_str,
        body={}
    ).execute()


@retry_with_backoff(allowed_errors=(APIError,))
def insert_data_with_service(service, sheet_id, start_cell, data):
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


@retry_with_backoff(allowed_errors=(APIError,))
def safe_write_log_to_sheet(*args, **kwargs):
    return write_log_to_sheet(*args, **kwargs)


def run_sync():
    client, raw_creds = get_gspread_and_raw_creds()
    core_handler = client.open_by_key(CORE_HANDLER_SHEET_ID)
    core = client.open_by_key(CORE_SHEET_ID)
    sheets_service = build('sheets', 'v4', credentials=raw_creds)

    ids_permissions = get_valid_business_ids(core_handler)

    for biz_index, (biz_id, permissions) in enumerate(ids_permissions):
        perms = ALL_PERMISSIONS if any(p.lower() == "all" for p in permissions) else permissions

        for perm_index, perm in enumerate(perms):
            if perm not in PERMISSION_SHEET_MAP:
                continue

            sheet_name, col_start, col_end = PERMISSION_SHEET_MAP[perm]

            try:
                # Delay slightly between permission syncs to avoid quota
                time.sleep(0.5 + random.uniform(0, 0.5))

                data = fetch_data(core, sheet_name, biz_id, col_start, col_end)
                if not data:
                    continue

                target_sheet = client.open_by_key(biz_id)

                # Calculate range width
                num_cols = max(len(row) for row in data)
                start_col_idx = ord("G")
                end_col_letter = chr(start_col_idx + num_cols - 1)
                range_to_clear = f"{sheet_name}!G11:{end_col_letter}"

                # Clear previous values
                clear_only_values_with_service(sheets_service, biz_id, range_to_clear)

                # Insert new data
                insert_data_with_service(sheets_service, biz_id, f"{sheet_name}!G11", data)

                # Log sync event
                safe_write_log_to_sheet(biz_id, sheet_name, raw_creds)

            except Exception as e:
                print(f"Error inserting into {sheet_name} for {biz_id}: {e}")

        # Optional delay between each business sync
        time.sleep(1 + random.uniform(0, 1))
