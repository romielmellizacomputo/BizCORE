# --- auth/google_auth.py ---
import os
import json
import gspread
from google.oauth2.service_account import Credentials


def get_gspread_and_raw_creds():
    sa_info = json.loads(os.getenv("BIZNEST_AGENT"))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(sa_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client, credentials
