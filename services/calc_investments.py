# --- services/calc_investments.py ---
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

def run_calculations():
    client, raw_creds = get_gspread_and_raw_creds()
    sheet = client.open_by_key(CORE_SHEET_ID)
    calc_investments(sheet, raw_creds)

if __name__ == "__main__":
    run_calculations()
