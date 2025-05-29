import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

def authenticate_from_github_secret(secret_name):
    secret = os.getenv(secret_name)
    if not secret:
        raise ValueError(f"GitHub secret {secret_name} not found.")
    credentials_info = json.loads(secret)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=credentials)
