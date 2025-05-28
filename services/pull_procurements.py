from auth.google_auth import authenticate_google_sheets
from config.settings import CORE_SHEET_ID

def fetch_procurements_data():
    service = authenticate_google_sheets()
    range_name = "Procurements!G4:W"
    result = service.spreadsheets().values().get(
        spreadsheetId=CORE_SHEET_ID, range=range_name
    ).execute()
    return result.get('values', [])
