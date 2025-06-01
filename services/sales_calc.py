# services/sales_calc.py
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

def calculate_sales():
    sheet, creds = get_gspread_and_raw_creds(CORE_SHEET_ID)
    sales_ws = sheet.worksheet("Sales")
    products_ws = sheet.worksheet("Products")
    sellers_ws = sheet.worksheet("Sellers")

    sales = sales_ws.get_all_values()[3:]
    products = {r[1]: parse_float(r[14]) for r in products_ws.get_all_values()[3:] if len(r) > 14}
    sellers = {r[6]: parse_float(r[13]) / 100 for r in sellers_ws.get_all_values()[3:] if len(r) > 13}

    unit_prices, total_amounts, discounts, vats, commissions, taxes, revenues = [], [], [], [], [], [], []

    for s in sales:
        product_id = s[11] if len(s) > 11 else ""
        qty = parse_float(s[14]) if len(s) > 14 else 0
        seller = s[9] if len(s) > 9 else ""

        price = products.get(product_id, 0)
        total = price * qty
        vat = total * (parse_float(s[18]) / 100 if len(s) > 18 else 0)
        amount = total + vat
        discount = amount * (parse_float(s[14]) / 100 if len(s) > 14 else 0)
        comm = amount * sellers.get(seller, 0)
        tax = (amount - discount - vat) * (parse_float(s[20]) / 100 if len(s) > 20 else 0)
        rev = amount - discount - vat - tax - comm

        unit_prices.append([round(price, 2)])
        total_amounts.append([round(amount, 2)])
        discounts.append([round(discount, 2)])
        vats.append([round(vat, 2)])
        commissions.append([round(comm, 2)])
        taxes.append([round(tax, 2)])
        revenues.append([round(rev, 2)])

    batch_update(CORE_SHEET_ID, "Sales!N4:N", unit_prices, creds)
    batch_update(CORE_SHEET_ID, "Sales!P4:P", total_amounts, creds)
    batch_update(CORE_SHEET_ID, "Sales!R4:R", discounts, creds)
    batch_update(CORE_SHEET_ID, "Sales!T4:T", vats, creds)
    batch_update(CORE_SHEET_ID, "Sales!I4:I", commissions, creds)
    batch_update(CORE_SHEET_ID, "Sales!V4:V", taxes, creds)
    batch_update(CORE_SHEET_ID, "Sales!W4:W", revenues, creds)

if __name__ == "__main__":
    calculate_sales()
