# File: services/sync_core.py
from config.settings import CORE_SHEET_ID, PERMISSIONS_SHEET_MAP
from auth.google_auth import get_google_sheets_service


FETCH_RANGES = {
    "Products": ("G4:U", "V"),
    "Sales": ("G4:T", "U"),
    "Procurements": ("G4:V", "W"),
    "Expenses": ("G4:T", "U"),
    "Suppliers": ("G4:R", "S"),
    "Resellers": ("G4:R", "S"),
    "Investments": ("G4:S", "T"),
    "Cash-Flow": ("G4:N", "O"),
    "Business Meetings": ("G4:N", "O"),
    "Business Goals": ("G4:N", "O")
}
