# File: auth/google_auth.py
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_google_sheets_service():
    creds_dict = json.loads(os.environ['BIZNEST_AGENT'])
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()
