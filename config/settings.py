# File: config/settings.py
import os

CORE_SHEET_ID = os.getenv("CORE")
CORE_HANDLER_ID = os.getenv("CORE_HANDLER")

PERMISSIONS_SHEET_MAP = {
    "Products": "pull_products",
    "Sales": "pull_revenue",
    "Procurements": "pull_procurements",
    "Expenses": "pull_expenses",
    "Suppliers": "pull_suppliers",
    "Resellers": "pull_resellers",
    "Investments": "pull_investments",
    "Cash-Flow": "pull_transactions",
    "Business Meetings": "pull_meetings",
    "Business Goals": "pull_goals"
}
