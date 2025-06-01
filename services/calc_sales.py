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
    body = {'valueInputOption': 'USER_ENTERED', 'data': [{'range': range_, 'values': values}]}
    service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

def calc_sales(sheet, creds):
    sales_ws = sheet.worksheet("Sales")
    products_ws = sheet.worksheet("Products")
    sellers_ws = sheet.worksheet("Sellers")

    sales_data = sales_ws.get_all_values()[3:]
    products_data = products_ws.get_all_values()[3:]
    sellers_data = sellers_ws.get_all_values()[3:]

    # Product prices
    product_price_map = {row[1]: parse_float(row[14]) for row in products_data if len(row) > 14}  # Products!O

    # Seller commission rate map
    seller_commission_map = {row[6]: parse_float(row[13]) / 100 for row in sellers_data if len(row) > 13}  # Sellers!N (13)

    unit_prices = []
    total_amounts = []
    revenues = []
    commission_values = []
    commissions_for_I = []
    discounts = []
    vat_values = []

    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""  # Sales!L
        quantity = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        seller_name = row[9] if len(row) > 9 else ""  # Sales!J

        unit_price = product_price_map.get(product_id, 0)
        total_amount = unit_price * quantity
        commission_rate = seller_commission_map.get(seller_name, 0)
        commission_value = total_amount * commission_rate

        discount_percentage = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        discount_value = total_amount * (discount_percentage / 100)
        
        vat_tax_percentage = parse_float(row[18]) if len(row) > 18 else 0  # Sales!S
        vat_value = total_amount * (vat_tax_percentage / 100)

        revenue = total_amount - discount_value - vat_value - commission_value

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        discounts.append([round(discount_value, 2)])
        vat_values.append([round(vat_value, 2)])
        commission_values.append([round(commission_value, 2)])
        commissions_for_I.append([round(commission_value, 2)])

    batch_update(sheet.id, "Sales!N4:N", unit_prices, creds)
    batch_update(sheet.id, "Sales!P4:P", total_amounts, creds)
    batch_update(sheet.id, "Sales!R4:R", discounts, creds)
    batch_update(sheet.id, "Sales!T4:T", vat_values, creds)
    batch_update(sheet.id, "Sales!I4:I", commission_values, creds)

def run_calculations():
    client, raw_creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_sales(sheet, raw_creds)

if __name__ == "__main__":
    run_calculations()
