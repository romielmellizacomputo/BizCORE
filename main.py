import os
import json
from datetime import datetime

from auth.google_auth import authenticate_google_sheets
from config.settings import CORE_HANDLER_SHEET_ID

from services.pull_products import fetch_products_data
from services.pull_sales import fetch_sales_data
from services.pull_procurements import fetch_procurements_data
from services.pull_expenses import fetch_expenses_data
from services.pull_suppliers import fetch_suppliers_data
from services.pull_resellers import fetch_resellers_data
from services.pull_investments import fetch_investments_data
from services.pull_transactions import fetch_cashflow_data
from services.pull_meetings import fetch_meetings_data
from services.pull_goals import fetch_goals_data


def get_active_child_sheets():
    service = authenticate_google_sheets()
    sheet = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=CORE_HANDLER_SHEET_ID,
        range="Settings!B3:I"
    ).execute()

    rows = result.get('values', [])
    today = datetime.today()

    children = []
    for row in rows:
        try:
            sheet_id = row[0].strip() if len(row) > 0 else None
            permissions_raw = row[5].strip() if len(row) > 5 else ""
            expiration_raw = row[7].strip() if len(row) > 7 else ""

            if not sheet_id or not permissions_raw:
                continue

            permissions = [p.strip() for p in permissions_raw.split(",") if p.strip()]
            if not permissions:
                continue

            if expiration_raw:
                try:
                    exp_date = datetime.strptime(expiration_raw, "%a, %b %d, %Y")
                    if exp_date < today:
                        continue
                except Exception as e:
                    print(f"⚠️ Skipping row with invalid date format: {expiration_raw}")
                    continue
            else:
                continue

            children.append({
                "sheet_id": sheet_id,
                "permissions": permissions
            })

        except Exception as e:
            print(f"⚠️ Skipping row due to parsing error: {e}")
            continue

    return children


def insert_into_child_sheets():
    children = get_active_child_sheets()
    print(f"Found {len(children)} valid child sheets.")

    service = authenticate_google_sheets()
    core_sheet_id = os.environ['CORE']

    sheets_config = {
        "Products": {
            "data_range": "Products!G4:U",
            "id_range": "Products!D4:D",
            "name_range": "Products!B4:B",
            "target_range": "Products!G11:V",
            "expected_data_columns": 15
        },
        "Sales": {
            "data_range": "Sales!G4:T",
            "id_range": "Sales!D4:D",
            "name_range": "Sales!B4:B",
            "target_range": "Sales!G11:U",
            "expected_data_columns": 14
        },
        "Procurements": {
            "data_range": "Procurements!G4:V",
            "id_range": "Procurements!D4:D",
            "name_range": "Procurements!B4:B",
            "target_range": "Procurements!G11:W",
            "expected_data_columns": 16
        },
        "Expenses": {
            "data_range": "Expenses!G4:T",
            "id_range": "Expenses!D4:D",
            "name_range": "Expenses!B4:B",
            "target_range": "Expenses!G11:U",
            "expected_data_columns": 14
        },
        "Suppliers": {
            "data_range": "Suppliers!G4:R",
            "id_range": "Suppliers!D4:D",
            "name_range": "Suppliers!B4:B",
            "target_range": "Suppliers!G11:S",
            "expected_data_columns": 12
        },
        "Resellers": {
            "data_range": "Resellers!G4:R",
            "id_range": "Resellers!D4:D",
            "name_range": "Resellers!B4:B",
            "target_range": "Resellers!G11:S",
            "expected_data_columns": 12
        },
        "Investments": {
            "data_range": "Investments!G4:S",
            "id_range": "Investments!D4:D",
            "name_range": "Investments!B4:B",
            "target_range": "Investments!G11:T",
            "expected_data_columns": 13
        },
        "Cash-Flow": {
            "data_range": "Cash-Flow!G4:N",
            "id_range": "Cash-Flow!D4:D",
            "name_range": "Cash-Flow!B4:B",
            "target_range": "Cash-Flow!G11:O",
            "expected_data_columns": 8
        },
        "Business Meetings": {
            "data_range": "Business Meetings!G4:N",
            "id_range": "Business Meetings!D4:D",
            "name_range": "Business Meetings!B4:B",
            "target_range": "Business Meetings!G11:O",
            "expected_data_columns": 8
        },
        "Business Goals": {
            "data_range": "Business Goals!G4:N",
            "id_range": "Business Goals!D4:D",
            "name_range": "Business Goals!B4:B",
            "target_range": "Business Goals!G11:O",
            "expected_data_columns": 8
        },
    }

    for child in children:
        child_id = child["sheet_id"]
        permissions = child["permissions"]
        print(f"\nProcessing child sheet: {child_id} with permissions: {permissions}")

        sheet_names = list(sheets_config.keys()) if "ALL" in permissions or "All" in permissions else permissions

        for sheet_name in sheet_names:
            if sheet_name not in sheets_config:
                print(f"⚠️ Skipping invalid permission: {sheet_name}")
                continue

            print(f"Processing sheet: {sheet_name}")
            config = sheets_config[sheet_name]

            id_vals = service.spreadsheets().values().get(
                spreadsheetId=core_sheet_id, range=config["id_range"]
            ).execute().get("values", [])
            data_vals = service.spreadsheets().values().get(
                spreadsheetId=core_sheet_id, range=config["data_range"]
            ).execute().get("values", [])
            name_vals = service.spreadsheets().values().get(
                spreadsheetId=core_sheet_id, range=config["name_range"]
            ).execute().get("values", [])

            expected_data_cols = config["expected_data_columns"]
            name_column_index = expected_data_cols  # Name goes at the end
            total_columns = expected_data_cols + 1

            matched_rows = []

            for idx, id_row in enumerate(id_vals):
                if id_row and id_row[0].strip() == child_id:
                    data = data_vals[idx] if idx < len(data_vals) else []
                    name = name_vals[idx][0] if idx < len(name_vals) and name_vals[idx] else ""

                    # Prepare row with proper size
                    row = [""] * total_columns

                    data_cursor = 0
                    for col in range(total_columns):
                        if col == name_column_index:
                            continue
                        if data_cursor < len(data):
                            row[col] = data[data_cursor]
                            data_cursor += 1

                    row[name_column_index] = name
                    matched_rows.append(row)

            if not matched_rows:
                print(f"🚫 No matching data for {sheet_name} in child {child_id}")
                continue

            print(f"✅ Inserting {len(matched_rows)} rows into {sheet_name} -> {config['target_range']}")

            # Clear existing data
            service.spreadsheets().values().clear(
                spreadsheetId=child_id,
                range=config["target_range"],
                body={}
            ).execute()

            # Write new data
            service.spreadsheets().values().update(
                spreadsheetId=child_id,
                range=config["target_range"],
                valueInputOption="RAW",
                body={"values": matched_rows}
            ).execute()


def main():
    print("Fetching Products Data...")
    print(f"Found {len(fetch_products_data())} records in Products")

    print("Fetching Sales Data...")
    print(f"Found {len(fetch_sales_data())} records in Sales")

    print("Fetching Procurements Data...")
    print(f"Found {len(fetch_procurements_data())} records in Procurements")

    print("Fetching Expenses Data...")
    print(f"Found {len(fetch_expenses_data())} records in Expenses")

    print("Fetching Suppliers Data...")
    print(f"Found {len(fetch_suppliers_data())} records in Suppliers")

    print("Fetching Resellers Data...")
    print(f"Found {len(fetch_resellers_data())} records in Resellers")

    print("Fetching Investments Data...")
    print(f"Found {len(fetch_investments_data())} records in Investments")

    print("Fetching Cash Flow Data...")
    print(f"Found {len(fetch_cashflow_data())} records in Cash-Flow")

    print("Fetching Business Meetings Data...")
    print(f"Found {len(fetch_meetings_data())} records in Business Meetings")

    print("Fetching Business Goals Data...")
    print(f"Found {len(fetch_goals_data())} records in Business Goals")

    print("Now inserting data into child sheets...")
    insert_into_child_sheets()


if __name__ == "__main__":
    main()
