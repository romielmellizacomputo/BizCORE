# File: auth/google_auth.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_google_sheets_service():
    credentials = service_account.Credentials.from_service_account_info(
        eval(os.environ['BIZNEST_AGENT']), scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=credentials).spreadsheets()
