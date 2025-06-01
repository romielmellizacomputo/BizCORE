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
    print("Fetching worksheets...")
    products_ws = sheet.worksheet("Products")
    sales_ws = sheet.worksheet("Sales")

    print("Fetching data...")
    products_data = products_ws.get_all_values()[3:]  # Products rows from 4 onwards
    sales_data = sales_ws.get_all_values()[3:]        # Sales rows from 4 onwards

    print(f"Loaded {len(products_data)} products, {len(sales_data)} sales rows")

    # Map product_id to total quantity sold (from Sales sheet)
    sales_qty_map = {}
    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""  # Sales!L
        quantity_sold = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        if product_id:
            sales_qty_map[product_id] = sales_qty_map.get(product_id, 0) + quantity_sold

    remaining_stocks = []
    vat_values = []
    total_costs = []
    unit_prices = []

    for row in products_data:
        product_id = row[1] if len(row) > 1 else ""     # Products!B
        quantity = parse_float(row[11]) if len(row) > 11 else 0  # Products!L
        unit_cost = parse_float(row[13]) if len(row) > 13 else 0  # Products!N
        shipping_fee = parse_float(row[17]) if len(row) > 17 else 0  # Products!R
        vat_rate = parse_float(row[14]) / 100 if len(row) > 14 else 0  # Products!O
        unit_price = parse_float(row[15]) if len(row) > 15 else 0  # Products!P

        total_sold_qty = sales_qty_map.get(product_id, 0)
        remaining_qty = quantity - total_sold_qty

        # VAT Value = Unit Price × VAT %
        vat_value = unit_price * vat_rate

        # Total Cost = (Unit Cost × Quantity) + Shipping Fee
        total_cost = (unit_cost * quantity) + shipping_fee

        # Unit Price = (Total Cost ÷ Quantity) + VAT Value
        calculated_unit_price = (total_cost / quantity) + vat_value if quantity else 0

        remaining_stocks.append([remaining_qty])
        vat_values.append([vat_value])
        total_costs.append([total_cost])
        unit_prices.append([calculated_unit_price])

    end_row = 3 + len(products_data)

    batch_update(sheet.id, f"Products!M4:M{end_row}", remaining_stocks, creds)     # Remaining Stocks
    batch_update(sheet.id, f"Products!Q4:Q{end_row}", vat_values, creds)           # VAT Value
    batch_update(sheet.id, f"Products!S4:S{end_row}", total_costs, creds)          # Total Cost
    batch_update(sheet.id, f"Products!P4:P{end_row}", unit_prices, creds)          # Unit Price


def run_calculations():
    print("Authenticating and opening sheet...")
    gc, creds = get_gspread_and_raw_creds()
    sheet = gc.open_by_key(CORE_SHEET_ID)
    calc_products(sheet, creds)
