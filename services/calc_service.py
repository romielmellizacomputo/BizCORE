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
    data = ws.get_all_values()[3:]
    total_cost_results = []
    remaining_results = []

    sales_ws = sheet.worksheet("Sales")
    sales_data = sales_ws.get_all_values()[3:]

    sales_qty_map = {}
    for sale in sales_data:
        product_id = sale[11] if len(sale) > 11 else ""
        qty_sold = parse_float(sale[14]) if len(sale) > 14 else 0
        if product_id:
            sales_qty_map[product_id] = sales_qty_map.get(product_id, 0) + qty_sold

    for row in data:
        try:
            quantity = parse_float(row[11]) if len(row) > 11 else 0
            unit_cost = parse_float(row[13]) if len(row) > 13 else 0
            shipping = parse_float(row[15]) if len(row) > 15 else 0
            product_id = row[1] if len(row) > 1 else ""

            total_cost = quantity * unit_cost + shipping
            total_cost_results.append([round(total_cost, 2)])

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

    product_price_map = {row[1]: parse_float(row[14]) for row in products_data if len(row) > 14}
    seller_commission_map = {row[6]: parse_float(row[13]) / 100 for row in sellers_data if len(row) > 13}

    unit_prices, total_amounts, discounts, vats = [], [], [], []
    commissions, income_taxes, revenues = [], [], []

    for row in sales_data:
        product_id = row[11] if len(row) > 11 else ""
        seller_name = row[9] if len(row) > 9 else ""
        quantity = parse_float(row[14]) if len(row) > 14 else 0
        discount_percent = parse_float(row[14]) if len(row) > 14 else 0
        vat_percent = parse_float(row[18]) if len(row) > 18 else 0
        income_tax_percent = parse_float(row[20]) if len(row) > 20 else 0

        unit_price = product_price_map.get(product_id, 0)
        total_sale = unit_price * quantity
        vat = total_sale * (vat_percent / 100)
        total_amount = total_sale + vat
        discount = total_amount * (discount_percent / 100)
        commission = total_amount * seller_commission_map.get(seller_name, 0)
        income_tax = (total_amount - discount - vat - commission) * (income_tax_percent / 100)

        revenue = total_amount - discount - vat - income_tax - commission

        unit_prices.append([round(unit_price, 2)])
        total_amounts.append([round(total_amount, 2)])
        discounts.append([round(discount, 2)])
        vats.append([round(vat, 2)])
        commissions.append([round(commission, 2)])
        income_taxes.append([round(income_tax, 2)])
        revenues.append([round(revenue, 2)])

    batch_update(sheet.id, "Sales!N4:N", unit_prices, creds)
    batch_update(sheet.id, "Sales!P4:P", total_amounts, creds)
    batch_update(sheet.id, "Sales!R4:R", discounts, creds)
    batch_update(sheet.id, "Sales!T4:T", vats, creds)
    batch_update(sheet.id, "Sales!I4:I", commissions, creds)
    batch_update(sheet.id, "Sales!V4:V", income_taxes, creds)
    batch_update(sheet.id, "Sales!W4:W", revenues, creds)

def calc_sellers(sheet, creds):
    sellers_ws = sheet.worksheet("Sellers")
    sales_ws = sheet.worksheet("Sales")

    sellers_data = sellers_ws.get_all_values()[3:]
    sales_data = sales_ws.get_all_values()[3:]

    items_sold, total_sales, commissions = [], [], []

    for seller_row in sellers_data:
        name = seller_row[6] if len(seller_row) > 6 else ""

        qty_sum, sale_sum, comm_sum = 0, 0, 0

        for sale in sales_data:
            if len(sale) > 7 and sale[7] == name:
                qty = parse_float(sale[14]) if len(sale) > 14 else 0
                sale_amt = parse_float(sale[15]) if len(sale) > 15 else 0
                comm = parse_float(sale[8]) if len(sale) > 8 else 0
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
            amount = parse_float(row[10]) if len(row) > 10 else 0
            rate = parse_float(row[13]) / 100 if len(row) > 13 else 0
            tax = parse_float(row[14]) / 100 if len(row) > 14 else 0

            interest = amount * rate
            taxed = interest * tax
            net = amount + (interest - taxed)
            results.append([round(net, 2)])
        except:
            results.append([""])

    batch_update(sheet.id, "Investments!P4:P", results, creds)

if __name__ == "__main__":
    run_calculations()
