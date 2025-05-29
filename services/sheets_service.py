from google_auth import get_gspread_service

class SheetsService:
    def __init__(self):
        self.service = get_gspread_service()
        self.spreadsheet = None

    def open_sheet(self, sheet_id):
        return self.service.spreadsheets().values()

    def get_sheet_values(self, sheet_id, range_name):
        result = self.service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        return result.get('values', [])

    def clear_range(self, sheet_id, range_name):
        self.service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=range_name).execute()

    def append_values(self, sheet_id, range_name, values):
        body = {'values': values}
        self.service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

    def update_values(self, sheet_id, range_name, values):
        body = {'values': values}
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
