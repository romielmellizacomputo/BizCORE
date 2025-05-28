# ============================
# utils/formatter.py (Optional, if you want to format date string)
# ============================
from datetime import datetime
import locale
locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

def is_not_expired(expiry_str):
    try:
        expiry_date = datetime.strptime(expiry_str, "%a, %b %d, %Y")
        return expiry_date >= datetime.today()
    except Exception:
        return False
