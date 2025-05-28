from services.pull_products import fetch_data as fetch_products
from services.pull_sales import fetch_data as fetch_sales
from services.pull_procurements import fetch_data as fetch_procurements
from services.pull_expenses import fetch_data as fetch_expenses
from services.pull_suppliers import fetch_data as fetch_suppliers
from services.pull_resellers import fetch_data as fetch_resellers
from services.pull_investments import fetch_data as fetch_investments
from services.pull_cash_flow import fetch_data as fetch_cash_flow
from services.pull_meetings import fetch_data as fetch_meetings
from services.pull_goals import fetch_data as fetch_goals

def main():
    products_data = fetch_products()
    sales_data = fetch_sales()
    procurements_data = fetch_procurements()
    expenses_data = fetch_expenses()
    suppliers_data = fetch_suppliers()
    resellers_data = fetch_resellers()
    investments_data = fetch_investments()
    cash_flow_data = fetch_cash_flow()
    meetings_data = fetch_meetings()
    goals_data = fetch_goals()

    # Process and insert data into child sheets as per your requirements

if __name__ == "__main__":
    main()
