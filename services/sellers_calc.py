# services/sellers_calc.py
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

def calculate_sellers():
    sheet, creds = get_gspread_and_raw_creds(CORE_SHEET_ID)
    sales = sheet.worksheet("Sales").get_all_values()[3:]
    sellers = sheet.worksheet("Sellers").get_all_values()[3:]

    sold_items, total_sales, commissions = [], [], []

    for seller in sellers:
        name = seller[6] if len(seller) > 6 else ""
        qty, total, comm = 0, 0, 0

        for sale in sales:
            if len(sale) > 7 and sale[7] == name:
                qty += parse_float(sale[14]) if len(sale) > 14 else 0
                total += parse_float(sale[18]) if len(sale) > 18 else 0
                comm += parse_float(sale[8]) if len(sale) > 8 else 0

        sold_items.append([qty])
        total_sales.append([round(total, 2)])
        commissions.append([round(comm, 2)])

    batch_update(CORE_SHEET_ID, "Sellers!L4:L", sold_items, creds)
    batch_update(CORE_SHEET_ID, "Sellers!M4:M", total_sales, creds)
    batch_update(CORE_SHEET_ID, "Sellers!O4:O", commissions, creds)

if __name__ == "__main__":
    calculate_sellers()
