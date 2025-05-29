# --- config/settings.py ---
import os

CORE_SHEET_ID = os.environ.get("CORE")
CORE_HANDLER_SHEET_ID = os.environ.get("CORE_HANDLER")

PERMISSION_SHEET_MAP = {
    "Products": ("Products", "G", "O"),
    "Sales": ("Sales", "G", "O"),
    "Procurements": ("Procurements", "G", "R"),
    "Expenses": ("Expenses", "G", "R"),
    "Suppliers": ("Suppliers", "G", "Q"),
    "Resellers": ("Resellers", "G", "O"),
    "Investments": ("Investments", "G", "P"),
    "Cash-Flow": ("Cash-Flow", "G", "L"),
    "Business Meetings": ("Business Meetings", "G", "N"),
    "Business Goals": ("Business Goals", "G", "N")
}

ALL_PERMISSIONS = list(PERMISSION_SHEET_MAP.keys())
