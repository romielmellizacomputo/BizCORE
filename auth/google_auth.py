import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ['BIZNEST_AGENT']),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build('sheets', 'v4', credentials=creds)
    return service
