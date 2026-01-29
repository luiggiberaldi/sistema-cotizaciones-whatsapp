import asyncio
import os
import sys

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.config.settings import settings
from supabase import create_client, Client

async def check_business_info():
    print("=== Checking Business Info Table ===")
    
    url = settings.supabase_url
    key = settings.supabase_service_key or settings.supabase_key # Prefer service key
    
    print(f"Connecting to Supabase: {url}")
    supabase: Client = create_client(url, key)
    
    try:
        print("Attempting to select from 'business_info'...")
        response = supabase.table("business_info").select("*").execute()
        
        data = response.data
        print(f"Response data: {data}")
        
        if not data:
            print("WARNING: Table exists but is EMPTY.")
        else:
            print(f"SUCCESS: Found {len(data)} records.")
            for item in data:
                print(f" - {item.get('key')}: {item.get('value')} (Category: {item.get('category')})")
                
    except Exception as e:
        print("ERROR: Could not query table.")
        print(e)
        print("\nPOSSIBLE CAUSE: Migration 006 has not been run or failed.")

if __name__ == "__main__":
    asyncio.run(check_business_info())
