# ============================
# config/settings.py
# ============================
import os

CORE_ID = os.getenv("CORE")
CORE_HANDLER_ID = os.getenv("CORE_HANDLER")

SHEET_MAPPINGS = {
    "Products": ("G", "U"),
    "Sales": ("G", "T"),
    "Procurements": ("G", "V"),
    "Expenses": ("G", "T"),
    "Suppliers": ("G", "R"),
    "Resellers": ("G", "R"),
    "Investments": ("G", "S"),
    "Cash-Flow": ("G", "N"),
    "Business Meetings": ("G", "N"),
    "Business Goals": ("G", "N")
}

ALL_SHEETS = list(SHEET_MAPPINGS.keys())
