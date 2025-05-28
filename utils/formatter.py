from datetime import datetime

def is_not_expired(expiry_date_str):
    """
    Checks if the expiry_date_str (e.g. "Thu, May 29, 2025") is today or in the future.
    Returns True if not expired, False if expired.
    """
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%a, %b %d, %Y")
        today = datetime.now()
        # Compare only date parts (ignore time)
        return expiry_date.date() >= today.date()
    except Exception as e:
        # If parsing fails, consider expired or log error
        return False

def parse_permissions(perm_str):
    """
    Parses the permissions string from a cell (like "Products, Sales") into a list.
    Handles cases like "ALL", "All", etc.
    """
    if not perm_str:
        return []
    perms = [p.strip().lower() for p in perm_str.split(',')]
    if 'all' in perms:
        return ['all']
    return perms

