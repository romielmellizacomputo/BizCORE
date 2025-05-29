from auth.google_auth import get_service
from config.settings import CORE_SHEET_ID, SHEET_RANGES, INSERT_START_ROW, SOURCE_BUSINESS_ID_COL, SOURCE_LABEL_COL

def fetch_and_insert(business_id, target_sheet_id, sheet_name="Business Meetings"):
    service = get_service()
    sheet_range = f"{sheet_name}!{SOURCE_BUSINESS_ID_COL}4:{SHEET_RANGES[sheet_name][-1]}"
    data = service.spreadsheets().values().get(spreadsheetId=CORE_SHEET_ID, range=sheet_range).execute().get("values", [])

    filtered_data = [row for row in data if len(row) >= 4 and row[3] == business_id]

    if not filtered_data:
        return

    values_to_insert = []
    for row in filtered_data:
        label = row[1] if len(row) > 1 else ""
        remaining = row[6:6+len(SHEET_RANGES[sheet_name].split(":"))]
        values_to_insert.append([label] + remaining)

    clear_range = f"{sheet_name}!G{INSERT_START_ROW}:{SHEET_RANGES[sheet_name][-1]}"
    insert_range = f"{sheet_name}!G{INSERT_START_ROW}"

    service.spreadsheets().values().clear(spreadsheetId=target_sheet_id, range=clear_range, body={}).execute()
    service.spreadsheets().values().update(
        spreadsheetId=target_sheet_id,
        range=insert_range,
        valueInputOption="RAW",
        body={"values": values_to_insert}
    ).execute()
