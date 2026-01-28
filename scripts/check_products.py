import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

target_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
supabase = create_client(SUPABASE_URL, target_key)

try:
    response = supabase.table("products").select("*").execute()
    products = response.data
    print(f"Productos encontrados: {len(products)}")
    for p in products:
        print(f"- {p['name']} (${p['price']})")
except Exception as e:
    print(f"Error consultando DB: {e}")
