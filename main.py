from services.sync_handler import get_valid_child_sheets
from services.sync_core import fetch_core_data, update_child_sheet
from config.settings import PERMISSIONS_SHEET_MAP


def main():
    valid_children = get_valid_child_sheets()

    for entry in valid_children:
        child_id = entry['child_id']
        permissions = entry['permissions']

        if "ALL" in [p.upper() for p in permissions]:
            sheets_to_pull = list(PERMISSIONS_SHEET_MAP.keys())
        else:
            sheets_to_pull = [p for p in permissions if p in PERMISSIONS_SHEET_MAP]

        for sheet_name in sheets_to_pull:
            data = fetch_core_data(sheet_name, child_id)
            if data:
                update_child_sheet(child_id, sheet_name, data)


if __name__ == '__main__':
    main()
