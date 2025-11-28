from jamaibase import JamAI

JAMAI_API_KEY = "jamai_pat_397772bdd7eb062a82d4f73d2123b0e991c4f5a5b75fdfec"
JAMAI_PROJECT_ID = "proj_58c8c327875e92a111420ea3"

client = JamAI(token=JAMAI_API_KEY, project_id=JAMAI_PROJECT_ID)

try:
    # Try to list tables. The method might be list_tables or similar on the table resource
    tables = client.table.list_tables(table_type="chat")
    print("Tables found:")
    for t in tables.items:
        print(f"- ID: {t.id}, Name: {t.id}") # Usually ID is the name or similar
except Exception as e:
    print(f"Error listing tables: {e}")
