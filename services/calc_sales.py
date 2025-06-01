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
        total_amount = unit_price * quantity
        commission_rate = seller_commission_map.get(seller_name, 0)
        commission_value = total_amount * commission_rate

        discount_percentage = parse_float(row[16]) if len(row) > 16 else 0  # Sales!Q
        discount_value = total_amount * (discount_percentage / 100)

        vat_tax_percentage = parse_float(row[18]) if len(row) > 18 else 0   # Sales!S
        vat_value = total_amount * (vat_tax_percentage / 100)

        revenue = total_amount - discount_value - vat_value - commission_value

        # New: Income Tax % is in Sales!U (index 20)
        income_tax_percentage = parse_float(row[20]) if len(row) > 20 else 0
        income_tax_value = revenue * (income_tax_percentage / 100)

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        discounts.append([round(discount_value, 2)])
        vat_values.append([round(vat_value, 2)])
        commission_values.append([round(commission_value, 2)])
        revenue_values.append([round(revenue, 2)])
        income_tax_values.append([round(income_tax_value, 2)])

        if i <= 7:  # Debug first few rows
            print(f"Row {i} => Product: {product_id}, Qty: {quantity}, Seller: {seller_name}")
            print(f"  Unit Price: {unit_price}, Total: {total_amount}")
            print(f"  Discount %: {discount_percentage}, Value: {discount_value}")
            print(f"  VAT %: {vat_tax_percentage}, Value: {vat_value}")
            print(f"  Commission %: {commission_rate}, Value: {commission_value}")
            print(f"  Revenue: {revenue}")
            print(f"  Income Tax %: {income_tax_percentage}, Value: {income_tax_value}")

    end_row = 4 + len(unit_prices) - 1

    batch_update(sheet.id, f"Sales!N4:N{end_row}", unit_prices, creds)        # Unit Price
    batch_update(sheet.id, f"Sales!P4:P{end_row}", total_amounts, creds)      # Total Amount
    batch_update(sheet.id, f"Sales!R4:R{end_row}", discounts, creds)          # Discount
    batch_update(sheet.id, f"Sales!T4:T{end_row}", vat_values, creds)         # VAT
    batch_update(sheet.id, f"Sales!I4:I{end_row}", commission_values, creds)  # Commission
    batch_update(sheet.id, f"Sales!V4:V{end_row}", income_tax_values, creds)  # Income Tax Value

def run_calculations():
    print("Authenticating and opening sheet...")
    client, creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_sales(sheet, creds)
    print("Calculation complete.")

if __name__ == "__main__":
    run_calculations()
