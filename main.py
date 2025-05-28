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

    # Next steps: Apply logic to match children IDs and insert into child sheets

if __name__ == "__main__":
    main()
