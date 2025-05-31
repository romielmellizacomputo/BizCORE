# --- services/calc_service.py ---
import os
from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID
from googleapiclient.discovery import build


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
    data = ws.get_all_values()[3:]  # Skip to row 4
    results = []

    for row in data:
        try:
            m = float(row[12]) if len(row) > 12 and row[12] else 0  # M
            l = float(row[11]) if len(row) > 11 and row[11] else 0  # L
            o = float(row[14]) if len(row) > 14 and row[14] else 0  # O
            total_cost = m * l + o
            results.append([round(total_cost, 2)])
        except:
            results.append([""])

    batch_update(sheet.id, "Products!P4:P", results, creds)


def calc_sales(sheet, creds):
    sales_ws = sheet.worksheet("Sales")
    products_ws = sheet.worksheet("Products")

    sales_data = sales_ws.get_all_values()[3:]  # Row 4 onwards
    products_data = products_ws.get_all_values()[3:]

    product_map = {row[1]: row[13] for row in products_data if len(row) > 13}  # B → N (unit price)

    unit_prices = []
    total_amounts = []
    revenues = []

    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""  # L
        quantity = float(row[14]) if len(row) > 14 and row[14] else 0  # O

        unit_price = float(product_map.get(product_id, 0))
        total_amount = unit_price * quantity

        try:
            q = float(row[16]) if len(row) > 16 else 0  # Q
            r = float(row[17]) if len(row) > 17 else 0  # R
            i = float(row[8]) if len(row) > 8 else 0    # I
        except:
            q = r = i = 0

        revenue = total_amount - (q + r + i)

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        revenues.append([round(revenue, 2)])

    batch_update(sheet.id, "Sales!N4:N", unit_prices, creds)
    batch_update(sheet.id, "Sales!P4:P", total_amounts, creds)
    batch_update(sheet.id, "Sales!S4:S", revenues, creds)


def calc_sellers(sheet, creds):
    sellers_ws = sheet.worksheet("Sellers")
    sales_ws = sheet.worksheet("Sales")

    sellers_data = sellers_ws.get_all_values()[3:]
    sales_data = sales_ws.get_all_values()[3:]

    items_sold = []
    total_sales = []
    commissions = []

    for seller_row in sellers_data:
        name = seller_row[6] if len(seller_row) > 6 else ""  # G

        qty_sum = 0
        sale_sum = 0
        comm_sum = 0

        for sale in sales_data:
            if len(sale) > 7 and sale[7] == name:  # H
                qty = float(sale[14]) if len(sale) > 14 and sale[14] else 0  # O
                sale_amt = float(sale[18]) if len(sale) > 18 and sale[18] else 0  # S
                comm = float(sale[8]) if len(sale) > 8 and sale[8] else 0  # I

                qty_sum += qty
                sale_sum += sale_amt
                comm_sum += comm

        items_sold.append([qty_sum])
        total_sales.append([round(sale_sum, 2)])
        commissions.append([round(comm_sum, 2)])

    batch_update(sheet.id, "Sellers!L4:L", items_sold, creds)
    batch_update(sheet.id, "Sellers!M4:M", total_sales, creds)
    batch_update(sheet.id, "Sellers!N4:N", commissions, creds)


def calc_investments(sheet, creds):
    ws = sheet.worksheet("Investments")
    data = ws.get_all_values()[3:]
    results = []

    for row in data:
        try:
            amount = float(row[10]) if len(row) > 10 else 0  # K
            rate = float(row[13].replace('%', '')) / 100 if len(row) > 13 else 0  # N
            tax = float(row[14].replace('%', '')) / 100 if len(row) > 14 else 0   # O

            interest = amount * rate
            taxed = interest * tax
            net = amount + (interest - taxed)
            results.append([round(net, 2)])
        except:
            results.append([""])

    batch_update(sheet.id, "Investments!P4:P", results, creds)


if __name__ == "__main__":
    run_calculations()
