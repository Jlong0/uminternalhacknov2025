from jamaibase import JamAI, protocol
import os

# Configuration from utils.py
JAMAI_API_KEY = "jamai_pat_665cc81ecae3eacc6c93f746dcf0670d88ae1b1199593d1f"
JAMAI_PROJECT_ID = "proj_383f190d307d0bded8d5e66c"

jamai_client = JamAI(token=JAMAI_API_KEY, project_id=JAMAI_PROJECT_ID)

print(f"Listing tables for Project: {JAMAI_PROJECT_ID}")

try:
    # List Action Tables
    print("\n--- Action Tables ---")
    action_tables = jamai_client.table.list_tables(table_type="action")
    for table in action_tables.items:
        print(f"ID: {table.id}, Name: {table.id}") # ID is usually the name

    # List Chat Tables
    print("\n--- Chat Tables ---")
    chat_tables = jamai_client.table.list_tables(table_type="chat")
    for table in chat_tables.items:
        print(f"ID: {table.id}, Name: {table.id}")

    # List Knowledge Tables
    print("\n--- Knowledge Tables ---")
    knowledge_tables = jamai_client.table.list_tables(table_type="knowledge")
    for table in knowledge_tables.items:
        print(f"ID: {table.id}, Name: {table.id}")

except Exception as e:
    print(f"Error listing tables: {e}")
