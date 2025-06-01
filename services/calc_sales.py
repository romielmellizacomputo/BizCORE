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
    result = service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
    print(f"Update result: {result}")

def calc_sales(sheet, creds):
    print("Fetching worksheets...")
    sales_ws = sheet.worksheet("Sales")
    products_ws = sheet.worksheet("Products")
    sellers_ws = sheet.worksheet("Sellers")

    print("Fetching data...")
    sales_data = sales_ws.get_all_values()[3:]      # Skip header rows (1–3)
    products_data = products_ws.get_all_values()[3:]
    sellers_data = sellers_ws.get_all_values()[3:]

    print(f"Loaded {len(sales_data)} sales rows, {len(products_data)} products, {len(sellers_data)} sellers")

    # Product prices map: Product ID (Products!B) => Unit Price (Products!O)
    product_price_map = {row[1]: parse_float(row[14]) for row in products_data if len(row) > 14}

    # Seller commissions: Seller Name (Sellers!G) => Commission % (Sellers!N)
    seller_commission_map = {row[6]: parse_float(row[13]) / 100 for row in sellers_data if len(row) > 13}

    unit_prices, total_amounts, discounts, vat_values = [], [], [], []
    commission_values, income_tax_values, revenues = [], [], []

    for i, row in enumerate(sales_data, start=4):
        product_id = row[11] if len(row) > 11 else ""        # Sales!L
        quantity = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        discount_percent = parse_float(row[15]) if len(row) > 15 else 0  # Sales!P
        seller_name = row[9] if len(row) > 9 else ""          # Sales!J
        vat_percent = parse_float(row[18]) if len(row) > 18 else 0       # Sales!S
        income_tax_percent = parse_float(row[20]) if len(row) > 20 else 0  # Sales!U

        unit_price = product_price_map.get(product_id, 0)
        total_sale = unit_price * quantity
        vat_value = total_sale * (vat_percent / 100)
        total_amount = total_sale + vat_value
        discount_value = total_amount * (discount_percent / 100)

        commission_rate = seller_commission_map.get(seller_name, 0)
        commission_value = total_amount * commission_rate

        income_tax_value = (total_amount - discount_value - vat_value - commission_value) * (income_tax_percent / 100)

        revenue = total_amount - discount_value - vat_value - commission_value - income_tax_value

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        discounts.append([round(discount_value, 2)])
        vat_values.append([round(vat_value, 2)])
        commission_values.append([round(commission_value, 2)])
        income_tax_values.append([round(income_tax_value, 2)])
        revenues.append([round(revenue, 2)])

        if i <= 7:  # Print first few rows for debug
            print(f"Row {i} => Product: {product_id}, Qty: {quantity}, Seller: {seller_name}")
            print(f"  Unit Price: {unit_price}, Total Sale: {total_sale}, VAT %: {vat_percent}, VAT: {vat_value}")
            print(f"  Total Amount: {total_amount}")
            print(f"  Discount %: {discount_percent}, Discount: {discount_value}")
            print(f"  Commission Rate: {commission_rate}, Commission: {commission_value}")
            print(f"  Income Tax %: {income_tax_percent}, Income Tax: {income_tax_value}")
            print(f"  Revenue: {revenue}")

    end_row = 4 + len(sales_data) - 1

    batch_update(sheet.id, f"Sales!N4:N{end_row}", unit_prices, creds)         # Unit Price
    batch_update(sheet.id, f"Sales!P4:P{end_row}", total_amounts, creds)       # Total Amount
    batch_update(sheet.id, f"Sales!R4:R{end_row}", discounts, creds)           # Discount
    batch_update(sheet.id, f"Sales!T4:T{end_row}", vat_values, creds)          # VAT
    batch_update(sheet.id, f"Sales!I4:I{end_row}", commission_values, creds)   # Commission
    batch_update(sheet.id, f"Sales!V4:V{end_row}", income_tax_values, creds)   # Income Tax
    batch_update(sheet.id, f"Sales!U4:U{end_row}", revenues, creds)            # Revenue

def run_calculations():
    print("Authenticating and opening sheet...")
    client, creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_sales(sheet, creds)
    print("Calculation complete.")

if __name__ == "__main__":
    run_calculations()
