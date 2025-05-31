# --- config/settings.py ---
import os

CORE_SHEET_ID = os.environ.get("CORE")
CORE_HANDLER_SHEET_ID = os.environ.get("CORE_HANDLER")

PERMISSION_SHEET_MAP = {
    "Products": ("Products", "G", "R"),         
    "Sales": ("Sales", "G", "W"),             
    "Expenses": ("Expenses", "G", "R"),       
    "Suppliers": ("Suppliers", "G", "R"),     
    "Sellers": ("Sellers", "G", "S"),          
    "Investments": ("Investments", "G", "T"), 
    "Cash-Flow": ("Cash-Flow", "G", "N"),      
    "Business Meetings": ("Business Meetings", "G", "O"),  
    "Business Goals": ("Business Goals", "G", "O")         
}

ALL_PERMISSIONS = list(PERMISSION_SHEET_MAP.keys())
