# services/investments_calc.py
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

def calculate_investments():
    sheet, creds = get_gspread_and_raw_creds(CORE_SHEET_ID)
    ws = sheet.worksheet("Investments")
    data = ws.get_all_values()[3:]

    returns = []
    for row in data:
        amount = parse_float(row[10]) if len(row) > 10 else 0
        rate = parse_float(row[13]) / 100 if len(row) > 13 else 0
        returns.append([round(amount * rate, 2)])

    batch_update(CORE_SHEET_ID, "Investments!P4:P", returns, creds)

if __name__ == "__main__":
    calculate_investments()
