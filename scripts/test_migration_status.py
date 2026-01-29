import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.config.database import get_supabase_client

async def test_join():
    supabase = get_supabase_client()
    print("Testing JOIN query with customers table...")
    try:
        # Try to select from quotes with join
        response = supabase.table('quotes').select('*, customers(full_name)').limit(1).execute()
        print("QUERY SUCCESSFUL!")
        print(f"Data: {response.data}")
    except Exception as e:
        print(f"QUERY FAILED")
        print(f"Error: {e}")
        print("\nPossible Cause: The 'customers' table does not exist or the foreign key is missing.")
        print("Solution: Please run 'migrations/008_create_customers_table.sql' in Supabase.")

if __name__ == "__main__":
    asyncio.run(test_join())
