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
    products_data = products_ws.get_all_values()[3:]  # Products rows from 4 onwards (index 3)
    sales_data = sales_ws.get_all_values()[3:]        # Sales rows from 4 onwards (index 3)

    print(f"Loaded {len(products_data)} products, {len(sales_data)} sales rows")

    # Map product_id to total quantity sold (from Sales sheet)
    sales_qty_map = {}
    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""  # Sales!L (index 11)
        quantity_sold = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O (index 14)
        if product_id:
            sales_qty_map[product_id] = sales_qty_map.get(product_id, 0) + quantity_sold

    remaining_stocks = []
    vat_values = []
    total_costs = []
    total_prices = []

    for row in products_data:
        product_id = row[1] if len(row) > 1 else ""            # Products!B (index 1)
        quantity = parse_float(row[11]) if len(row) > 11 else 0   # Products!L (index 11)
        unit_cost = parse_float(row[13]) if len(row) > 13 else 0  # Products!N (index 13)
        shipping_fee = parse_float(row[17]) if len(row) > 17 else 0  # Products!R (index 17)
        vat_rate = parse_float(row[14]) / 100 if len(row) > 14 else 0  # Products!O (index 14)
        selling_price = parse_float(row[15]) if len(row) > 15 else 0   # Products!P (index 15)

        total_sold_qty = sales_qty_map.get(product_id, 0)
        remaining_qty = quantity - total_sold_qty

        # Total Cost = (Unit Cost × Quantity) + Shipping Fee
        total_cost = (unit_cost * quantity) + shipping_fee

        # VAT per unit = (Total Cost / Quantity) * VAT Rate
        vat_value = ((total_cost / quantity) * vat_rate) if quantity else 0

        # Total Price = Selling Price + VAT Value
        total_price = selling_price + vat_value

        remaining_stocks.append([remaining_qty])
        vat_values.append([vat_value])
        total_costs.append([total_cost])
        total_prices.append([total_price])

    end_row = 3 + len(products_data)

    batch_update(sheet.id, f"Products!M4:M{end_row}", remaining_stocks, creds)     # Remaining Stocks (M column)
    batch_update(sheet.id, f"Products!Q4:Q{end_row}", total_prices, creds)         # Total Price (Q column)
    batch_update(sheet.id, f"Products!R4:R{end_row}", vat_values, creds)           # VAT Value (R column)
    batch_update(sheet.id, f"Products!S4:S{end_row}", total_costs, creds)          # Total Cost (S column)

def run_calculations():
    print("Authenticating and opening sheet...")
    gc, creds = get_gspread_and_raw_creds()
    sheet = gc.open_by_key(CORE_SHEET_ID)
    update_products(sheet, creds)
