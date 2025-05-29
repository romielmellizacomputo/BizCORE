# File: services/data_sync.py
import os
import json
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
from utils.logger import get_logger

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
logger = get_logger(__name__)

# Mapping of sheet names to their respective data ranges
SHEET_RANGES = {
    'Products': 'H10:P10',
    'Sales': 'H10:P10',
    'Procurements': 'H10:S10',
    'Expenses': 'H10:S10',
    'Suppliers': 'H10:R10',
    'Resellers': 'H10:P10',
    'Investments': 'H10:Q10',
    'Cash-Flow': 'H10:M10',
    'Business Meetings': 'H10:O10',
    'Business Goals': 'H10:O10'
}

DASHBOARD_CELLS = ['H3', 'H5', 'M5']

class GoogleSheetService:
    def __init__(self):
        service_account_info = json.loads(os.environ['BIZNEST_AGENT'])
        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=creds)

    def get_values(self, spreadsheet_id, range_name):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])

    def write_values(self, spreadsheet_id, range_name, values):
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': values}
        ).execute()

    def append_values(self, spreadsheet_id, range_name, values):
        self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()


def generate_reference(sheet_name, existing_refs):
    while True:
        ref = f"SEPA-{uuid.uuid4().hex[:8].upper()}"
        if ref not in existing_refs:
            return ref


def sync_data(trigger_sheet_id, trigger_sheet_name):
    gs = GoogleSheetService()
    db_sheet_id = os.environ['CORE']

    dashboard_values = [gs.get_values(trigger_sheet_id, cell) for cell in DASHBOARD_CELLS]
    dashboard_values = [val[0][0] if val else '' for val in dashboard_values]  # H3, H5, M5

    if trigger_sheet_name not in SHEET_RANGES:
        logger.error(f"Unsupported sheet name: {trigger_sheet_name}")
        return

    data_range = SHEET_RANGES[trigger_sheet_name]
    data_rows = gs.get_values(trigger_sheet_id, data_range)

    core_data = gs.get_values(db_sheet_id, f"{trigger_sheet_name}!B4:B")  # Column B = Reference No
    existing_refs = [row[0] for row in core_data if row]

    final_rows = []

    for i, row in enumerate(data_rows):
        ref = row[0] if row else ''
        if not ref:  # New row
            ref = generate_reference(trigger_sheet_name, existing_refs)
            existing_refs.append(ref)
            values = [ref] + dashboard_values + row[1:]
            gs.append_values(db_sheet_id, f"{trigger_sheet_name}!B4", [values])
            gs.write_values(trigger_sheet_id, f"H3", [[f"Inserted: {ref}"]])
        else:  # Update
            if ref in existing_refs:
                row_idx = existing_refs.index(ref) + 4
                values = [ref] + dashboard_values + row[1:]
                gs.write_values(db_sheet_id, f"{trigger_sheet_name}!B{row_idx}", [values])
                gs.write_values(trigger_sheet_id, f"H3", [[f"Updated: {ref}"]])

    logger.info("Sync completed successfully")
