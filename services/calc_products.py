# --- services/calc_products.py ---
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

def calc_products(sheet, creds):
    ws = sheet.worksheet("Products")
    data = ws.get_all_values()[3:]  # Start from row 4
    total_cost_results = []
    remaining_results = []

    # Fetch sales data to compute remaining stocks
    sales_ws = sheet.worksheet("Sales")
    sales_data = sales_ws.get_all_values()[3:]

    # Build a map of total sold quantity per product ID from Sales sheet
    sales_qty_map = {}
    for sale in sales_data:
        product_id = sale[11] if len(sale) > 11 else ""  # Sales!L
        qty_sold = parse_float(sale[14]) if len(sale) > 14 else 0  # Sales!O
        if product_id:
            sales_qty_map[product_id] = sales_qty_map.get(product_id, 0) + qty_sold

    for row in data:
        try:
            quantity = parse_float(row[11]) if len(row) > 11 else 0     # Products!L
            unit_cost = parse_float(row[13]) if len(row) > 13 else 0    # Products!N
            extra_cost = parse_float(row[15]) if len(row) > 15 else 0   # Products!P
            product_id = row[1] if len(row) > 1 else ""                 # Products!B

            # Total Cost = Quantity * Unit Cost + Extra Cost
            total_cost = quantity * unit_cost + extra_cost
            total_cost_results.append([round(total_cost, 2)])

            # Remaining Stocks = Quantity - Total Sold
            total_sold = sales_qty_map.get(product_id, 0)
            remaining = quantity - total_sold
            remaining_results.append([round(remaining, 2)])
        except:
            total_cost_results.append([""])
            remaining_results.append([""])

    batch_update(sheet.id, "Products!Q4:Q", total_cost_results, creds)
    batch_update(sheet.id, "Products!M4:M", remaining_results, creds)

def run_calculations():
    client, raw_creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_products(sheet, raw_creds)

if __name__ == "__main__":
    run_calculations()
