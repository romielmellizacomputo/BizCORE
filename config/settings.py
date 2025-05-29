import os

CORE_SHEET_ID = os.getenv("CORE")
CORE_HANDLER_SHEET_ID = os.getenv("CORE_HANDLER")

SHEET_RANGES = {
    "Products": "G:O",
    "Sales": "G:O",
    "Procurements": "G:R",
    "Expenses": "G:R",
    "Suppliers": "G:Q",
    "Resellers": "G:O",
    "Investments": "G:P",
    "Cash-Flow": "G:L",
    "Business Meetings": "G:N",
    "Business Goals": "G:N"
}

INSERT_START_ROW = 11
SOURCE_BUSINESS_ID_COL = "D"
SOURCE_LABEL_COL = "B"
