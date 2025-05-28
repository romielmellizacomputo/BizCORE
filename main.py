# main.py
import json
from auth.google_auth import authenticate_gsheet
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID
from datetime import datetime
from googleapiclient.errors import HttpError

def fetch_children_ids_and_permissions(service, core_handler_id):
    try:
        result = service.spreadsheets().values().get(spreadsheetId=core_handler_id, range='Settings!B3:I').execute()
        rows = result.get('values', [])
        
        valid_ids = []
        today = datetime.today().date()

        for row in rows:
            if len(row) < 8:  # Ensure there are enough columns
                continue
            child_id = row[0]
            expiration_date = row[6]
            permissions = row[5].split(', ')  # Assuming permissions are comma-separated
            
            if expiration_date:
                exp_date = datetime.strptime(expiration_date, '%a, %b %d, %Y').date()
                if exp_date >= today and any(perm in permissions for perm in ["Products", "Sales", "Procurements", "Expenses", "Suppliers", "Resellers", "Investments", "Cash-Flow", "Business Meetings", "Business Goals", "ALL"]):
                    valid_ids.append((child_id, permissions))
        
        return valid_ids

    except HttpError as err:
        print(f"An error occurred: {err}")
        return []

def main():
    # Load the service account JSON from GitHub secrets
    with open('path_to_your_service_account.json') as json_file:
        secret_json = json.load(json_file)

    service = authenticate_gsheet(secret_json)
    
    valid_children = fetch_children_ids_and_permissions(service, CORE_HANDLER_SHEET_ID)
    
    for child_id, permissions in valid_children:
        # Here you will implement the logic to fetch data from CORE based on the permissions
        # and insert it into the child sheets.
        pass  # Replace with your logic to handle data fetching and insertion.

if __name__ == "__main__":
    main()
