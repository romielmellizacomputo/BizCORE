import os
from datetime import datetime
from utils import formatter
from services.sheets_service import SheetsService
from config import settings

# Initialize services
sheets_service = SheetsService()

def get_business_sheet_ids():
    # Fetch data from CORE_HANDLER's Settings sheet
    range_settings = "Settings!B3:I"  # assuming headers in row 2, data starts from row 3
    values = sheets_service.get_sheet_values(settings.CORE_HANDLER, range_settings)

    today_str = datetime.today().strftime("%a, %b %d, %Y")
    valid_ids = []

    for row in values:
        if len(row) >= 9:
            sheet_id = row[1]
            expiration_date_str = row[8]
            permission_str = row[6] if len(row) > 6 else ''
            last_updated_str = row[7] if len(row) > 7 else ''

            # Check expiration
            if not formatter.is_expired(expiration_date_str):
                # Check permissions
                permissions = formatter.parse_permissions(permission_str)
                if permissions:
                    valid_ids.append({
                        'sheet_id': sheet_id,
                        'permissions': permissions
                    })
    return valid_ids

def get_data_from_core(sheet_id, sheet_name, id_value, columns_range):
    # Fetch data from core sheet
    range_name = f"{sheet_name}!D4:D"  # D column for IDs
    all_ids = sheets_service.get_sheet_values(sheet_id, range_name)

    data = []
    for idx, row in enumerate(all_ids):
        if row and row[0] == id_value:
            # Fetch the row data
            row_range = f"{sheet_name}!B{idx+4}:{columns_range}"
            row_data = sheets_service.get_sheet_values(sheet_id, row_range)
            if row_data:
                data.append(row_data[0])
    return data

def process_sheet(target_sheet_id, sheet_name, data_rows, source_columns_range):
    # Clear existing data
    sheets_service.clear_range(target_sheet_id, f"{sheet_name}!G11:Z")
    # Prepare data to insert
    insert_data = []
    for row in data_rows:
        # Map data: B -> G, then G:O etc.
        # We need to align columns carefully
        # For simplicity, creating a row with 10 columns (G to P)
        mapped_row = [''] * 10
        # B column is index 0 in row
        if len(row) >= 1:
            mapped_row[0] = row[0]  # B to G
        # G:O (columns 6-14) from source
        # assuming row[6:15]
        source_cols = row[6:15]
        for idx, val in enumerate(source_cols):
            if idx + 1 < len(mapped_row):
                mapped_row[idx + 1] = val
        insert_data.append(mapped_row)
    # Insert data starting at G11
    if insert_data:
        sheets_service.update_values(target_sheet_id, f"{sheet_name}!G11", insert_data)

def main():
    business_sheets = get_business_sheet_ids()
    # Map permission to sheets
    permission_map = {
        "products": "Products",
        "sales": "Sales",
        "procurements": "Procurements",
        "expenses": "Expenses",
        "suppliers": "Suppliers",
        "resellers": "Resellers",
        "investments": "Investments",
        "cash-flow": "Cash-Flow",
        "business meetings": "Business Meetings",
        "business goals": "Business Goals",
        "all": ["Products", "Sales", "Procurements", "Expenses", "Suppliers", "Resellers", "Investments", "Cash-Flow", "Business Meetings", "Business Goals"]
    }

    for entry in business_sheets:
        sheet_id = entry['sheet_id']
        permissions = entry['permissions']
        if 'all' in permissions:
            sheets_to_process = permission_map['all']
        else:
            sheets_to_process = [perm for perm in permissions if perm in permission_map]
        for sheet_name in sheets_to_process:
            # Fetch data for each sheet based on business ID
            data_rows = get_data_from_core(settings.CORE, sheet_name, sheet_id, "G:O")
            # Determine columns range based on sheet
            if sheet_name in ["Products", "Sales", "Resellers"]:
                columns_range = "G:O"
            elif sheet_name in ["Procurements", "Expenses"]:
                columns_range = "G:R"
            elif sheet_name == "Suppliers":
                columns_range = "G:Q"
            elif sheet_name == "Investments":
                columns_range = "G:P"
            elif sheet_name == "Cash-Flow":
                columns_range = "G:L"
            elif sheet_name == "Business Meetings":
                columns_range = "G:N"
            elif sheet_name == "Business Goals":
                columns_range = "G:N"
            else:
                columns_range = "G:Z"

            process_sheet(sheet_id, sheet_name, data_rows, columns_range)

if __name__ == "__main__":
    main()
