import gspread
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("path/to/your/service_account.json", scope)
    client = gspread.authorize(creds)
    return client
