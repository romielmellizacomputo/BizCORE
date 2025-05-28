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
            permissions = row[6].split(",") if len(row) > 6 else []
            expiration = row[7] if len(row) > 7 else None

            if expiration:
                exp_date = datetime.strptime(expiration.strip(), "%a, %b %d, %Y")
                if exp_date < today:
                    continue
            else:
                continue

            cleaned_permissions = [p.strip() for p in permissions]
            children.append({
                "sheet_id": sheet_id,
                "permissions": cleaned_permissions
            })
        except Exception as e:
            print(f"Skipping row due to error: {e}")
            continue

    return children


def insert_into_child_sheets():
    children = get_active_child_sheets()
    print(f"Found {len(children)} valid child sheets.")

    all_data = {
        "Products": fetch_products_data(),
        "Sales": fetch_sales_data(),
        "Procurements": fetch_procurements_data(),
        "Expenses": fetch_expenses_data(),
        "Suppliers": fetch_suppliers_data(),
        "Resellers": fetch_resellers_data(),
        "Investments": fetch_investments_data(),
        "Cash-Flow": fetch_cashflow_data(),
        "Business Meetings": fetch_meetings_data(),
        "Business Goals": fetch_goals_data()
    }

    column_ranges = {
        "Products": "G11:U",
        "Sales": "G11:T",
        "Procurements": "G11:V",
        "Expenses": "G11:T",
        "Suppliers": "G11:R",
        "Resellers": "G11:R",
        "Investments": "G11:S",
        "Cash-Flow": "G11:N",
        "Business Meetings": "G11:N",
        "Business Goals": "G11:N"
    }

    service = authenticate_google_sheets()

    for child in children:
        child_id = child["sheet_id"]
        permissions = child["permissions"]

        if "ALL" in permissions or "All" in permissions:
            perms = list(all_data.keys())
        else:
            perms = [p for p in permissions if p in all_data]

        for sheet_name in perms:
            data = all_data[sheet_name]
            matched_rows = []

            for row in data:
                if len(row) >= 1 and row[0].strip() == child_id:
                    matched_rows.append(row)

            if not matched_rows:
                print(f"No data to insert for {sheet_name} in child {child_id}")
                continue

            insert_range = f"{sheet_name}!{column_ranges[sheet_name]}"
            print(f"Clearing {insert_range} in child sheet {child_id}...")
            service.spreadsheets().values().clear(
                spreadsheetId=child_id,
                range=insert_range,
                body={}
            ).execute()

            print(f"Inserting {len(matched_rows)} rows into {insert_range} in child sheet {child_id}")
            service.spreadsheets().values().update(
                spreadsheetId=child_id,
                range=insert_range,
                valueInputOption="RAW",
                body={"values": matched_rows}
            ).execute()


def main():
    print("Fetching Products Data...")
    products = fetch_products_data()
    print(f"Found {len(products)} records in Products")

    print("Fetching Sales Data...")
    sales = fetch_sales_data()
    print(f"Found {len(sales)} records in Sales")

    print("Fetching Procurements Data...")
    procurements = fetch_procurements_data()
    print(f"Found {len(procurements)} records in Procurements")

    print("Fetching Expenses Data...")
    expenses = fetch_expenses_data()
    print(f"Found {len(expenses)} records in Expenses")

    print("Fetching Suppliers Data...")
    suppliers = fetch_suppliers_data()
    print(f"Found {len(suppliers)} records in Suppliers")

    print("Fetching Resellers Data...")
    resellers = fetch_resellers_data()
    print(f"Found {len(resellers)} records in Resellers")

    print("Fetching Investments Data...")
    investments = fetch_investments_data()
    print(f"Found {len(investments)} records in Investments")

    print("Fetching Cash Flow Data...")
    cashflow = fetch_cashflow_data()
    print(f"Found {len(cashflow)} records in Cash-Flow")

    print("Fetching Business Meetings Data...")
    meetings = fetch_meetings_data()
    print(f"Found {len(meetings)} records in Business Meetings")

    print("Fetching Business Goals Data...")
    goals = fetch_goals_data()
    print(f"Found {len(goals)} records in Business Goals")

    print("Now inserting data into child sheets...")
    insert_into_child_sheets()


if __name__ == "__main__":
    main()
