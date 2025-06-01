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

def calc_sellers(sheet, creds):
    sellers_ws = sheet.worksheet("Sellers")
    sales_ws = sheet.worksheet("Sales")

    sellers_data = sellers_ws.get_all_values()[3:]
    sales_data = sales_ws.get_all_values()[3:]

    items_sold = []
    total_sales = []
    commissions = []

    for seller_row in sellers_data:
        name = seller_row[6] if len(seller_row) > 6 else ""  # Sellers!G

        qty_sum = 0
        sale_sum = 0
        comm_sum = 0

        for sale in sales_data:
            if len(sale) > 7 and sale[7] == name:  # Sales!H matches Sellers!G
                qty = parse_float(sale[14]) if len(sale) > 14 else 0  # Sales!O
                sale_amt = parse_float(sale[18]) if len(sale) > 18 else 0  # Sales!P
                comm = parse_float(sale[8]) if len(sale) > 8 else 0  # Sales!I

                qty_sum += qty
                sale_sum += sale_amt
                comm_sum += comm

        items_sold.append([qty_sum])
        total_sales.append([round(sale_sum, 2)])
        commissions.append([round(comm_sum, 2)])

    batch_update(sheet.id, "Sellers!L4:L", items_sold, creds)
    batch_update(sheet.id, "Sellers!M4:M", total_sales, creds)
    batch_update(sheet.id, "Sellers!O4:O", commissions, creds)

def run_calculations():
    client, raw_creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_sellers(sheet, raw_creds)

if __name__ == "__main__":
    run_calculations()
