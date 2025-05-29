import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_gspread_service():
    service_account_info = os.environ['BIZNEST_AGENT']
    creds_info = json.loads(service_account_info)
    credentials = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=credentials)
    return service
