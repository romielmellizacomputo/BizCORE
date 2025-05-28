import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def authenticate_google_sheets():
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.environ['BIZNEST_AGENT']),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service
