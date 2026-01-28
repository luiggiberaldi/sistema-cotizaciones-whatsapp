from src.infrastructure.config.settings import Settings
import os

print("--- Environment Variables ---")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY: {'*' * 5 if os.getenv('SUPABASE_KEY') else 'None'}")
print(f"SUPABASE_JWT_SECRET: {'*' * 5 if os.getenv('SUPABASE_JWT_SECRET') else 'None'}")
print(f"SECRET_KEY: {'*' * 5 if os.getenv('SECRET_KEY') else 'None'}")
print("-" * 30)

try:
    settings = Settings()
    print("Settings loaded successfully!")
except Exception as e:
    print(f"Settings validation failed:\n{e}")
