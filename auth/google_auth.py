# auth/google_auth.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

def authenticate_gsheet(secret_json):
    credentials = service_account.Credentials.from_service_account_info(secret_json)
    service = build('sheets', 'v4', credentials=credentials)
    return service
