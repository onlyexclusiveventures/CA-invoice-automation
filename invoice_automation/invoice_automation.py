import requests
import json
import os

# Notion API setup
NOTION_API_KEY = os.getenv("NOTION_API_KEY")  # Use environment variable for security
T_CA_INVOICES_DATABASE_ID = "151404f6b69e81158d0de23c708168d4"  # (t) (CA) Invoices Database ID
OEV_INVOICES_DATABASE_ID = "155404f6-b69e-80f7-a0a5-db58eda0c82a"  # OEV Invoices Database ID
EMPLOYEE_DATABASE_ID = "150404f6b69e805bbc9fda05fb334aaf"  # Employee Directory Database ID

# File to store processed page IDs
PROCESSED_PAGES_FILE = "processed_pages.json"

# Load processed page IDs
def load_processed_pages():
    if os.path.exists(PROCESSED_PAGES_FILE):
        with open(PROCESSED_PAGES_FILE, "r", encoding="utf-8") as file:
            processed_pages = json.load(file)
            print(f"Loaded processed pages: {processed_pages}")
            return processed_pages
    print("No processed_pages.json file found, starting with an empty list.")
    return []

# Save a processed page ID
def save_processed_page(page_id):
    processed_pages = load_processed_pages()
    if page_id not in processed_pages:
        processed_pages.append(page_id)
        with open(PROCESSED_PAGES_FILE, "w", encoding="utf-8") as file:
            json.dump(processed_pages, file, indent=4)
        print(f"Saved processed page ID: {page_id}")
    else:
        print(f"Page ID {page_id} is already in the processed list.")

# The rest of your existing functions (get_employee_id, get_latest_invoice, etc.) remain unchanged

# Example usage
employee_name = "Bobby"
invoice_page = get_latest_invoice()

if invoice_page:
    invoice_fields = extract_invoice_fields(invoice_page)
    employee_id = get_employee_id(employee_name)
    if employee_id:
        employer_id = invoice_fields.get('Employer ID', "")
        create_invoice(invoice_fields, employee_id, employer_id)
    else:
        print(f"Employee {employee_name} not found!")
else:
    print("No invoice with 'Payment Processing' status found!")
