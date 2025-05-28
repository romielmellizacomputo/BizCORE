# ============================
# services/pull_products.py (Similar for other pull_*.py)
# ============================
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.base_puller import fetch_and_push_data

def main():
    fetch_and_push_data("Products")

if __name__ == '__main__':
    main()
