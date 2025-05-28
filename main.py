# main.py
import json
from auth.google_auth import authenticate_gsheet
from config.settings import CORE_SHEET_ID, CORE_HANDLER_SHEET_ID
from datetime import datetime
from googleapiclient.errors import HttpError
from services.pull_products import fetch_products_data
from services.pull_sales import fetch_sales_data
from services.pull_procurements import fetch_procurements_data
from services.pull_expenses import fetch_expenses_data
from services.pull_suppliers import fetch_suppliers_data
from services.pull_resellers import fetch_resellers_data
from services.pull_investments import fetch_investments_data
from services.pull_cash_flow import fetch_cash_flow_data
from services.pull_meetings import fetch_meetings_data
from services.pull_goals import fetch_goals_data

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

def insert_data_to_child_sheet(service, child_id, data, range_start):
    try:
        # Clear previous data
        service.spreadsheets().values().clear(spreadsheetId=child_id, range=range_start).execute()
        
        # Insert new data
        body = {
            'values': data
        }
        service.spreadsheets().values().update(spreadsheetId=child_id, range=range_start, valueInputOption='RAW', body=body).execute()
    except HttpError as err:
        print(f"An error occurred while inserting data: {err}")

def main():
    # Load the service account JSON from GitHub secrets
    with open('path_to_your_service_account.json') as json_file:
        secret_json = json.load(json_file)

    service = authenticate_gsheet(secret_json)
    
    valid_children = fetch_children_ids_and_permissions(service, CORE_HANDLER_SHEET_ID)
    
    for child_id, permissions in valid_children:
        all_data = []
        
        if "Products" in permissions or "ALL" in permissions:
            products_data = fetch_products_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(products_data)
            insert_data_to_child_sheet(service, child_id, products_data, 'G11:U')

        if "Sales" in permissions or "ALL" in permissions:
            sales_data = fetch_sales_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(sales_data)
            insert_data_to_child_sheet(service, child_id, sales_data, 'G11:T')

        if "Procurements" in permissions or "ALL" in permissions:
            procurements_data = fetch_procurements_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(procurements_data)
            insert_data_to_child_sheet(service, child_id, procurements_data, 'G11:V')

        if "Expenses" in permissions or "ALL" in permissions:
            expenses_data = fetch_expenses_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(expenses_data)
            insert_data_to_child_sheet(service, child_id, expenses_data, 'G11:T')

        if "Suppliers" in permissions or "ALL" in permissions:
            suppliers_data = fetch_suppliers_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(suppliers_data)
            insert_data_to_child_sheet(service, child_id, suppliers_data, 'G11:R')

        if "Resellers" in permissions or "ALL" in permissions:
            resellers_data = fetch_resellers_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(resellers_data)
            insert_data_to_child_sheet(service, child_id, resellers_data, 'G11:R')

        if "Investments" in permissions or "ALL" in permissions:
            investments_data = fetch_investments_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(investments_data)
            insert_data_to_child_sheet(service, child_id, investments_data, 'G11:S')

        if "Cash-Flow" in permissions or "ALL" in permissions:
            cash_flow_data = fetch_cash_flow_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(cash_flow_data)
            insert_data_to_child_sheet(service, child_id, cash_flow_data, 'G11:N')

        if "Business Meetings" in permissions or "ALL" in permissions:
            meetings_data = fetch_meetings_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(meetings_data)
            insert_data_to_child_sheet(service, child_id, meetings_data, 'G11:N')

        if "Business Goals" in permissions or "ALL" in permissions:
            goals_data = fetch_goals_data(service, CORE_SHEET_ID, child_id)
            all_data.extend(goals_data)
            insert_data_to_child_sheet(service, child_id, goals_data, 'G11:N')

if __name__ == "__main__":
    main()
