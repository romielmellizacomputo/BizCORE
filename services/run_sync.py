from config.settings import SHEETS, TARGET_START_ROW
from services.fetch_children import fetch_active_children
from services.insert_data import clear_and_insert

# Import all pullers
from services.pull_products import fetch_products
from services.pull_sales import fetch_sales
from services.pull_procurements import fetch_procurements
from services.pull_expenses import fetch_expenses
from services.pull_suppliers import fetch_suppliers
from services.pull_resellers import fetch_resellers
from services.pull_investments import fetch_investments
from services.pull_transactions import fetch_transactions
from services.pull_meetings import fetch_meetings
from services.pull_goals import fetch_goals

# Map permission names to fetch functions and target sheet names (assuming same)
PERMISSION_FETCH_MAP = {
    'products': fetch_products,
    'sales': fetch_sales,
    'procurements': fetch_procurements,
    'expenses': fetch_expenses,
    'suppliers': fetch_suppliers,
    'resellers': fetch_resellers,
    'investments': fetch_investments,
    'cash-flow': fetch_transactions,
    'business meetings': fetch_meetings,
    'business goals': fetch_goals,
    'all': None,  # special handling
}

def col_letter_to_index(letter):
    return ord(letter.upper()) - ord('A') + 1

def run():
    children = fetch_active_children()
    print(f"Found {len(children)} active children")

    for child in children:
        child_id = child['child_id']
        perms = [p.lower() for p in child['permissions']]

        # If ALL present, override to all keys except 'all'
        if 'all' in perms:
            perms = [k for k in PERMISSION_FETCH_MAP.keys() if k != 'all']

        for perm in perms:
            if perm not in PERMISSION_FETCH_MAP:
                print(f"Unknown permission {perm} for child {child_id}")
                continue

            fetch_func = PERMISSION_FETCH_MAP[perm]
            if not fetch_func:
                continue

            print(f"Fetching {perm} data for child {child_id}...")
            data = fetch_func(child_id)

            if not data:
                print(f"No data found for {perm} and child {child_id}")
                continue

            # Get column range from SHEETS config
            col_range = SHEETS.get(perm.capitalize(), None)
            if not col_range:
                print(f"No column config for {perm}")
                continue

            col_start, col_end = col_range.split(":")
            # Insert B column data to col after last
            # Last col is col_end, B is 2, we want B data to col_end + 1
            # But per instructions, insert fetched columns from G:U etc starting row 11,
            # and insert the B column value into the column immediately after last col
            # The fetch data rows contain B plus the range (B..U), so B is first col

            # Separate B column data
            b_col_data = [[row[0]] if len(row) > 0 else [''] for row in data]

            # Insert B column data to column after col_end
            next_col_index = col_letter_to_index(col_end) + 1
            next_col_letter = chr(ord('A') + next_col_index - 1)

            # Insert B data
            print(f"Inserting B column data to {next_col_letter}{TARGET_START_ROW} for child {child_id} perm {perm}")
            clear_and_insert(child_id, perm.capitalize(), TARGET_START_ROW, next_col_letter, next_col_letter, b_col_data)

            # Insert G:U etc data starting at col_start, row 11
            # Extract columns G:U data (which excludes B col)
            # In fetched data rows, after B is columns from G onwards (positions 1 onwards for G:U)
            g_u_data = [row[1:] if len(row) > 1 else [] for row in data]

            print(f"Inserting G:U data to {perm.capitalize()}!{col_start}{TARGET_START_ROW} for child {child_id}")
            clear_and_insert(child_id, perm.capitalize(), TARGET_START_ROW, col_start, col_end, g_u_data)

if __name__ == "__main__":
    run()
