from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    # Get JSON content from environment variable (GitHub secret)
    service_account_info = json.loads(os.environ['BIZNEST_AGENT'])
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service
