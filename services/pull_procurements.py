# services/pull_procurements.py
def fetch_procurements_data(service, core_sheet_id, child_id):
    try:
        result = service.spreadsheets().values().get(spreadsheetId=core_sheet_id, range='Procurements!G4:V').execute()
        rows = result.get('values', [])
        
        # Filter rows where the business ID matches child_id
        filtered_data = [row for row in rows if row[0] == child_id]  # Assuming B is the first column in the range
        
        return filtered_data
    except Exception as e:
        print(f"Error fetching procurements data: {e}")
        return []
