import os

CORE_SHEET_ID = os.getenv('CORE')              # Main CORE sheet ID
CORE_HANDLER_SHEET_ID = os.getenv('CORE_HANDLER')  # Sheet with children IDs and permissions

# Sheets to handle
SHEETS = {
    "Products": "G:U",
    "Sales": "G:T",
    "Procurements": "G:V",
    "Expenses": "G:T",
    "Suppliers": "G:R",
    "Resellers": "G:R",
    "Investments": "G:S",
    "Cash-Flow": "G:N",
    "Business Meetings": "G:N",
    "Business Goals": "G:N",
}

START_ROW = 4  # data start row in core sheets
TARGET_START_ROW = 11  # target sheets clear & insert start row
