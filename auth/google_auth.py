# --- auth/google_auth.py ---
import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    biznest_agent = os.environ.get("BIZNEST_AGENT")
    if not biznest_agent:
        raise EnvironmentError("BIZNEST_AGENT secret not found")

    service_account_info = json.loads(biznest_agent)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(credentials)
