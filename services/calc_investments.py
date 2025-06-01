import os
from auth.google_auth import get_gspread_and_raw_creds
from config.settings import CORE_SHEET_ID
from googleapiclient.discovery import build

def parse_float(val):
    try:
        # Remove commas and percent signs, convert to float
        return float(val.replace(',', '').replace('%', '').strip()) if val else 0
    except:
        return 0

def batch_update(sheet_id, range_, values, creds):
    service = build('sheets', 'v4', credentials=creds)
    body = {'valueInputOption': 'USER_ENTERED', 'data': [{'range': range_, 'values': values}]}
    service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

def calc_investments(sheet, creds):
    print("Fetching Investments worksheet...")
    invest_ws = sheet.worksheet("Investments")

    print("Fetching data from Investments sheet...")
    data = invest_ws.get_all_values()[3:]  # Rows from 4 onwards (index 3)

    print(f"Loaded {len(data)} rows from Investments")

    proceeds_values = []

    for row in data:
        investment_amount = parse_float(row[10])  # K column is index 10
        interest_rate = parse_float(row[13]) / 100  # N column is index 13 (convert % to decimal)
        tax_rate = parse_float(row[14]) / 100       # O column is index 14 (convert % to decimal)

        interest_amount = investment_amount * interest_rate
        net = interest_amount * tax_rate
        proceeds = investment_amount + net

        proceeds_values.append([round(proceeds, 2)])  # Round to 2 decimals for clarity

    end_row = 3 + len(data)  # Because data starts from row 4 (index 3)

    print(f"Updating Proceeds column P4:P{end_row} with calculated values...")
    batch_update(sheet.id, f"Investments!P4:P{end_row}", proceeds_values, creds)
    print("Update complete.")

def run_calculations():
    print("Authenticating and opening sheet...")
    gc, creds = get_gspread_and_raw_creds()
    sheet = gc.open_by_key(CORE_SHEET_ID)
    calc_investments(sheet, creds)
