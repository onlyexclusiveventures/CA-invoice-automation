import requests
import json
import os

# Notion API setup
NOTION_API_KEY = "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"  # Your Notion API key
T_CA_INVOICES_DATABASE_ID = "151404f6b69e81158d0de23c708168d4"  # (t) (CA) Invoices Database ID
OEV_INVOICES_DATABASE_ID = "155404f6-b69e-80f7-a0a5-db58eda0c82a"  # OEV Invoices Database ID (corrected UUID format)
EMPLOYEE_DATABASE_ID = "150404f6b69e805bbc9fda05fb334aaf"  # Employee Directory Database ID

# File to store processed page IDs
PROCESSED_PAGES_FILE = "processed_pages.json"

# Load processed page IDs
def load_processed_pages():
    if os.path.exists(PROCESSED_PAGES_FILE):
        with open(PROCESSED_PAGES_FILE, "r") as file:
            return json.load(file)
    return []

# Save a processed page ID
def save_processed_page(page_id):
    processed_pages = load_processed_pages()
    if page_id not in processed_pages:
        processed_pages.append(page_id)
        with open(PROCESSED_PAGES_FILE, "w") as file:
            json.dump(processed_pages, file)

# Get employee ID by employee name
def get_employee_id(employee_name):
    url = f"https://api.notion.com/v1/databases/{EMPLOYEE_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "property": "Name",
            "title": {
                "equals": employee_name
            }
        }
    }

    print(f"Sending request to fetch employee ID for {employee_name}...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            employee_id = results[0]['id']
            print(f"Employee ID found: {employee_id}")
            return employee_id
    else:
        print(f"Error fetching employee ID: {response.status_code}")
        print(f"Error details: {response.text}")

    return None

# Get the latest invoice with 'Payment Processing' status
def get_latest_invoice():
    url = f"https://api.notion.com/v1/databases/{T_CA_INVOICES_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "property": "Status",
            "select": {
                "equals": "Payment Processing"
            }
        },
        "sorts": [
            {
                "property": "Date Issued",
                "direction": "descending"
            }
        ],
        "page_size": 1
    }

    print("Sending request to fetch invoice with 'Payment Processing' status...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        results = response.json().get("results", [])
        processed_pages = load_processed_pages()
        for invoice_page in results:
            page_id = invoice_page['id']
            if page_id not in processed_pages:
                print(f"Fetched new invoice: {invoice_page}")
                return invoice_page
        print("No new invoices found.")
    else:
        print(f"Error fetching invoices: {response.status_code}")
        print(f"Error details: {response.text}")

    return None

# Extract the necessary fields from the invoice data
def extract_invoice_fields(invoice_data):
    props = invoice_data['properties']
    page_id = invoice_data['id']

    name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
    status = props.get('Status', {}).get('select', {}).get('name', '')
    date_issued = props.get('Date Issued', {}).get('date', {}).get('start', '')
    date_due = props.get('Date Due', {}).get('date', {}).get('start', '')
    sum_value = props.get('Sum', {}).get('number', 0)
    employer_relations = props.get('Employer', {}).get('relation', [])
    employer_id = employer_relations[0]['id'] if employer_relations else ""

    return {
        "Page ID": page_id,
        "Name": name,
        "Status": status,
        "Date Issued": date_issued,
        "Date Due": date_due,
        "Sum": sum_value,
        "Employer ID": employer_id
    }

# Create an invoice in the OEV Invoices database
def create_invoice(invoice_fields, employee_id, employer_id):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {
            "database_id": OEV_INVOICES_DATABASE_ID
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": invoice_fields.get('Name', 'Untitled')
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": invoice_fields.get('Status', 'Payment Processing')
                }
            },
            "Date Issued": {
                "date": {
                    "start": invoice_fields.get('Date Issued', '')
                }
            },
            "Date Due": {
                "date": {
                    "start": invoice_fields.get('Date Due', '')
                }
            },
            "Employee": {
                "relation": [
                    {
                        "id": employee_id
                    }
                ]
            },
            "Employer": {
                "relation": [
                    {
                        "id": employer_id
                    }
                ]
            },
            "Sum": {
                "number": invoice_fields.get('Sum', 0)
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Invoice '{invoice_fields.get('Name')}' created successfully!")
        save_processed_page(invoice_fields.get('Page ID'))
    else:
        print(f"Error creating invoice '{invoice_fields.get('Name')}': {response.text}")

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
