from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json

def get_service():
    credentials_json = os.getenv("BIZNEST_AGENT")
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(credentials_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=credentials)
