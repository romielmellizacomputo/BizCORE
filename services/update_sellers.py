# --- services/calc_sellers.py ---
import os
from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID
from googleapiclient.discovery import build

def parse_float(val):
    try:
        return float(val.replace(',', '').replace('%', '').strip()) if val else 0
    except:
        return 0

def batch_update(sheet_id, range_, values, creds):
    service = build('sheets', 'v4', credentials=creds)
    body = {'valueInputOption': 'USER_ENTERED', 'data': [{'range': range_, 'values': values}]}
    service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

def update_sellers(sheet, creds):
    print("Fetching worksheets...")
    sellers_ws = sheet.worksheet("Sellers")
    sales_ws = sheet.worksheet("Sales")

    print("Fetching data...")
    sellers_data = sellers_ws.get_all_values()[3:]  # Sellers rows from 4 onwards (index 3)
    sales_data = sales_ws.get_all_values()[3:]      # Sales rows from 4 onwards (index 3)

    print(f"Loaded {len(sellers_data)} sellers, {len(sales_data)} sales rows")

    # Map seller name to sums: total sold items, total sales, total commissions
    # Sales sheet: seller name col H (index 7), sold items col O (index 14),
    # total sales col P (index 15), commissions col I (index 8)

    seller_totals = {}

    for row in sales_data:
        seller_name = row[7] if len(row) > 7 else ""
        sold_items = parse_float(row[14]) if len(row) > 14 else 0
        total_sales = parse_float(row[15]) if len(row) > 15 else 0
        commissions = parse_float(row[8]) if len(row) > 8 else 0

        if seller_name:
            if seller_name not in seller_totals:
                seller_totals[seller_name] = {'sold_items': 0, 'total_sales': 0, 'commissions': 0}
            seller_totals[seller_name]['sold_items'] += sold_items
            seller_totals[seller_name]['total_sales'] += total_sales
            seller_totals[seller_name]['commissions'] += commissions

    total_sold_items_list = []
    total_sales_list = []
    total_commissions_list = []

    for row in sellers_data:
        seller_name = row[6] if len(row) > 6 else ""  # Sellers!G (index 6)
        totals = seller_totals.get(seller_name, {'sold_items': 0, 'total_sales': 0, 'commissions': 0})

        total_sold_items_list.append([totals['sold_items']])
        total_sales_list.append([totals['total_sales']])
        total_commissions_list.append([totals['commissions']])

    end_row = 3 + len(sellers_data)  # Because data starts at row 4

    batch_update(sheet.id, f"Sellers!L4:L{end_row}", total_sold_items_list, creds)   # Total Sold Items (L)
    batch_update(sheet.id, f"Sellers!M4:M{end_row}", total_sales_list, creds)        # Total Sales (M)
    batch_update(sheet.id, f"Sellers!O4:O{end_row}", total_commissions_list, creds)  # Total Commissions (O)


def run_calculations():
    print("Authenticating and opening sheet...")
    gc, creds = get_gspread_and_raw_creds()
    sheet = gc.open_by_key(CORE_SHEET_ID)
    update_products(sheet, creds)
    update_sellers(sheet, creds)

