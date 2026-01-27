
content = """SUPABASE_URL="https://ikuliolpnpfitngurexm.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrdWxpb2xwbnBmaXRuZ3VyZXhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1MzYzNTYsImV4cCI6MjA4NTExMjM1Nn0.1RrQOeW4sohR1AfxsxYheeCbxUKGvAL_tUhm_lClVcc"
SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrdWxpb2xwbnBmaXRuZ3VyZXhtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTUzNjM1NiwiZXhwIjoyMDg1MTEyMzU2fQ.DbEoD6463wrgskjH5JHQL5EndG0zSQI29scsOM_RLyM"
SUPABASE_JWT_SECRET="y6oBrMJ91NGFiCdPCSumcRRc/CDxLsg5THW7SzVqSSW92+7lI8DW+2W5dkaRMH/yKLoX36xobyT9OEYpqWMU8g=="
WHATSAPP_VERIFY_TOKEN="token_prueba_local"
WHATSAPP_ACCESS_TOKEN="simulated_token"
WHATSAPP_PHONE_NUMBER_ID="123456789"
SECRET_KEY="super-secret-dev-key-12345"
"""
with open(".env", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated .env file with UTF-8 encoding")
