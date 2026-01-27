import asyncio
import requests
import json
from supabase import create_client, Client

# Config (Hardcoded for verification script)
SUPABASE_URL = "https://ikuliolpnpfitngurexm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrdWxpb2xwbnBmaXRuZ3VyZXhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1MzYzNTYsImV4cCI6MjA4NTExMjM1Nn0.1RrQOeW4sohR1AfxsxYheeCbxUKGvAL_tUhm_lClVcc"
API_URL = "http://localhost:8000/api/v1/quotes/"

async def verify_flow():
    print("1. Iniciando sesion con Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    email = "luiggiberaldi94@gmail.com"
    password = "password123"
    
    try:
        # Sign in
        print(f"   Intentando login con {email}...")
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session = res.session
        access_token = session.access_token
        print("   [OK] Login exitoso! Token obtenido.")
        
        # Call Backend API
        print("\n2. Consultando Backend API (GET /api/v1/quotes/)...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(API_URL, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   [OK] Respuesta exitosa!")
            print(f"   Total cotizaciones: {data.get('total', 0)}")
            quotes = data.get('quotes', [])
            for q in quotes:
                print(f"    - ID: {q.get('id')} | Cliente: {q.get('client_phone')} | Total: {q.get('total')} | Status: {q.get('status')}")
        else:
            print("   [ERROR] Error en la peticion API")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   [ERROR] Fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_flow())
