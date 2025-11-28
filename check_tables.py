from jamaibase import JamAI
import os

# Credentials from utils.py
JAMAI_API_KEY = "jamai_pat_fa3fdd2a5013689a34d4eb46882a780cae2b842e8837a8d3"
JAMAI_PROJECT_ID = "proj_afdc5e38e0195ad1f761c509"

client = JamAI(token=JAMAI_API_KEY, project_id=JAMAI_PROJECT_ID)

try:
    # Try to list chat tables
    print("Fetching Action Tables...")
    tables = client.table.list_tables(table_type="action")
    for t in tables.items:
        print(f"Found Action Table: {t.id}")

    print("\nFetching Chat Tables...")
    tables = client.table.list_tables(table_type="chat")
    for t in tables.items:
        print(f"Found Chat Table: {t.id}")
        
    print("\nFetching Knowledge Tables...")
    tables = client.table.list_tables(table_type="knowledge")
    for t in tables.items:
        print(f"Found Knowledge Table: {t.id}")

except Exception as e:
    print(f"Error: {e}")
