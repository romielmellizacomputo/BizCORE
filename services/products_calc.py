# services/products_calc.py
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

def calculate_products():
    sheet, creds = get_gspread_and_raw_creds(CORE_SHEET_ID)
    ws = sheet.worksheet("Products")
    data = ws.get_all_values()[3:]

    sales_ws = sheet.worksheet("Sales")
    sales_data = sales_ws.get_all_values()[3:]

    sales_map = {}
    for sale in sales_data:
        product_id = sale[11] if len(sale) > 11 else ""
        qty = parse_float(sale[14]) if len(sale) > 14 else 0
        sales_map[product_id] = sales_map.get(product_id, 0) + qty

    total_costs = []
    remaining_stocks = []

    for row in data:
        qty = parse_float(row[11]) if len(row) > 11 else 0
        unit_cost = parse_float(row[13]) if len(row) > 13 else 0
        extra_cost = parse_float(row[15]) if len(row) > 15 else 0
        product_id = row[1] if len(row) > 1 else ""

        total_cost = qty * unit_cost + extra_cost
        total_costs.append([round(total_cost, 2)])

        total_sold = sales_map.get(product_id, 0)
        remaining = qty - total_sold
        remaining_stocks.append([round(remaining, 2)])

    batch_update(CORE_SHEET_ID, "Products!Q4:Q", total_costs, creds)
    batch_update(CORE_SHEET_ID, "Products!M4:M", remaining_stocks, creds)

if __name__ == "__main__":
    calculate_products()
