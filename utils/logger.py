# --- utils/logger.py ---
from datetime import datetime
from pytz import timezone
from googleapiclient.discovery import build

def get_ph_timestamp():
    ph_time = datetime.now(timezone("Asia/Manila"))
    return ph_time.strftime("%B %d, %Y at %-I:%M %p")  # Example: May 20, 2025 at 2:57 PM


def write_log_to_sheet(sheet_id, sheet_name, creds):
    try:
        service = build('sheets', 'v4', credentials=creds)
        now_ph = datetime.now(timezone('Asia/Manila'))
        timestamp = now_ph.strftime("%B %d, %Y at %-I:%M %p")
        log_message = f"{sheet_name} was updated on {timestamp} - PH Time"

        # Write log message to H3
        range_ = f"{sheet_name}!H3"
        values = [[log_message]]
        body = {"values": values}

        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

    except Exception as e:
        print(f"Failed to write log to {sheet_name} H3: {e}")
