# --- utils/logger.py ---
from datetime import datetime
from pytz import timezone


def get_ph_timestamp():
    ph_time = datetime.now(timezone("Asia/Manila"))
    return ph_time.strftime("%B %d, %Y at %-I:%M %p")  # Example: May 20, 2025 at 2:57 PM


def write_log_to_sheet(sheet, worksheet_name):
    try:
        ph_time_str = get_ph_timestamp()
        log_message = f"{worksheet_name} was updated on {ph_time_str} - PH Time"
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.update("H3", log_message)
    except Exception as e:
        print(f"Failed to write log to {worksheet_name} H3: {e}")
