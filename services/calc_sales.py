# --- services/calc_sales.py ---

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
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': [{'range': range_, 'values': values}]
    }
    print(f"Updating range {range_} with {len(values)} rows...")
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body=body
    ).execute()
    print(f"Update result: {result}")

def calc_sales(sheet, creds):
    print("Fetching worksheets...")
    sales_ws = sheet.worksheet("Sales")
    products_ws = sheet.worksheet("Products")
    sellers_ws = sheet.worksheet("Sellers")

    print("Fetching data...")
    sales_data = sales_ws.get_all_values()[3:]
    products_data = products_ws.get_all_values()[3:]
    sellers_data = sellers_ws.get_all_values()[3:]

    print(f"Loaded {len(sales_data)} sales rows, {len(products_data)} products, {len(sellers_data)} sellers")

    product_price_map = {row[1]: parse_float(row[14]) for row in products_data if len(row) > 14}
    seller_commission_map = {row[6]: parse_float(row[13]) / 100 for row in sellers_data if len(row) > 13}

    unit_prices = []
    total_amounts = []
    discounts = []
    vat_values = []
    commission_values = []
    revenue_values = []
    income_tax_values = []

    for i, row in enumerate(sales_data, start=4):
        product_id = row[11] if len(row) > 11 else ""       # Sales!L
        quantity = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        seller_name = row[9] if len(row) > 9 else ""        # Sales!J

        unit_price = product_price_map.get(product_id, 0)
        subtotal = unit_price * quantity

        vat_tax_percentage = parse_float(row[18]) if len(row) > 18 else 0   # Sales!S
        vat_value = subtotal * (vat_tax_percentage / 100)

        total_amount = subtotal + vat_value

        commission_rate = seller_commission_map.get(seller_name, 0)
        commission_value = total_amount * commission_rate

        discount_percentage = parse_float(row[16]) if len(row) > 16 else 0  # Sales!Q
        discount_value = total_amount * (discount_percentage / 100)

        revenue = total_amount - discount_value - commission_value

        income_tax_percentage = parse_float(row[20]) if len(row) > 20 else 0
        income_tax_value = revenue * (income_tax_percentage / 100)

        unit_prices.append([unit_price])
        total_amounts.append([total_amount])
        discounts.append([discount_value])
        vat_values.append([vat_value])
        commission_values.append([commission_value])
        revenue_values.append([revenue])
        income_tax_values.append([income_tax_value])

    end_row = 3 + len(sales_data)

    batch_update(sheet.id, f"Sales!N4:N{end_row}", unit_prices, creds)        # Unit Price
    batch_update(sheet.id, f"Sales!P4:P{end_row}", total_amounts, creds)      # Total Amount
    batch_update(sheet.id, f"Sales!R4:R{end_row}", discounts, creds)          # Discount Value
    batch_update(sheet.id, f"Sales!T4:T{end_row}", vat_values, creds)         # VAT Value
    batch_update(sheet.id, f"Sales!I4:I{end_row}", commission_values, creds)  # Commission Value
    batch_update(sheet.id, f"Sales!V4:V{end_row}", income_tax_values, creds)  # Income Tax Value
    batch_update(sheet.id, f"Sales!W4:W{end_row}", revenue_values, creds)     # Revenue (Net)

def run_calculations():
    print("Authenticating and opening sheet...")
    gc, creds = get_gspread_and_raw_creds()
    sheet = gc.open_by_key(CORE_SHEET_ID)
    calc_sales(sheet, creds)
