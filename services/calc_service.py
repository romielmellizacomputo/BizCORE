# --- services/calc_service.py ---
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


def run_calculations():
    client, raw_creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)

    calc_products(sheet, raw_creds)
    calc_sales(sheet, raw_creds)
    calc_sellers(sheet, raw_creds)
    calc_investments(sheet, raw_creds)


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

    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""  # Sales!L
        quantity = parse_float(row[14]) if len(row) > 14 else 0  # Sales!O
        seller_name = row[9] if len(row) > 9 else ""  # Sales!J

        unit_price = product_price_map.get(product_id, 0)
        total_amount = unit_price * quantity
        commission_rate = seller_commission_map.get(seller_name, 0)
        commission_value = total_amount * commission_rate

        q = parse_float(row[16]) if len(row) > 16 else 0  # Sales!Q
        r = parse_float(row[17]) if len(row) > 17 else 0  # Sales!R
        i = parse_float(row[8]) if len(row) > 8 else 0    # Sales!I

        revenue = total_amount - (q + r + i)

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        revenues.append([round(revenue, 2)])
        commission_values.append([round(commission_value, 2)])
        commissions_for_I.append([round(commission_value, 2)])

    batch_update(sheet.id, "Sales!N4:N", unit_prices, creds)
    batch_update(sheet.id, "Sales!P4:P", total_amounts, creds)
    batch_update(sheet.id, "Sales!S4:S", revenues, creds)
    batch_update(sheet.id, "Sales!O4:O", commission_values, creds)
    batch_update(sheet.id, "Sales!I4:I", commissions_for_I, creds)

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
                sale_amt = parse_float(sale[18]) if len(sale) > 18 else 0  # Sales!S
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


def calc_investments(sheet, creds):
    ws = sheet.worksheet("Investments")
    data = ws.get_all_values()[3:]
    results = []

    for row in data:
        try:
            amount = parse_float(row[10]) if len(row) > 10 else 0  # K
            rate = parse_float(row[13]) / 100 if len(row) > 13 else 0  # N
            tax = parse_float(row[14]) / 100 if len(row) > 14 else 0   # O

            interest = amount * rate
            taxed = interest * tax
            net = amount + (interest - taxed)
            results.append([round(net, 2)])
        except:
            results.append([""])

    batch_update(sheet.id, "Investments!P4:P", results, creds)


if __name__ == "__main__":
    run_calculations()
