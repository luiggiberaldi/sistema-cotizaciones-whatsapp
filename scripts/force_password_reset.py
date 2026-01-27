import asyncio
import os
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.config.settings import settings
from supabase import create_client, Client

async def main():
    print("Intentando restablecer contraseña vía Admin API...")
    
    # Check for service key
    if not settings.supabase_service_key:
        print("[ERROR] SUPABASE_SERVICE_KEY no esta configurada en .env.")
        print("Necesitas la 'service_role' key de Supabase (Project Settings -> API) para esta operacion.")
        return

    # Initialize Supabase with Service Key (Bypasses RLS and Auth rules)
    supabase: Client = create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )
    
    email = "luiggiberaldi94@gmail.com"
    new_password = "password123"
    
    try:
        # Get user by email to find ID
        print(f"Buscando usuario {email}...")
        # Note: listing users requires admin privileges
        # supabase-py doesn't always expose list_users easily in older versions, 
        # but modern ones have supabase.auth.admin.list_users()
        
        # Alternative: Try to update directly if library supports it, or search
        # Let's try listing first
        users_response = supabase.auth.admin.list_users()
        user_id = None
        
        for user in users_response:
            if user.email == email:
                user_id = user.id
                break
        
        if not user_id:
            print(f"[ERROR] Usuario {email} no encontrado.")
            return

        print(f"Usuario encontrado. ID: {user_id}")
        print(f"Estableciendo contrasena a: '{new_password}'...")
        
        # Update password
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        
        print("\n[OK] Contrasena actualizada exitosamente!")
        print(f"Email: {email}")
        print(f"Password: {new_password}")
        print("Intenta iniciar sesion ahora con estas credenciales.")

    except Exception as e:
        print(f"\n[ERROR] Error durante el proceso: {e}")

if __name__ == "__main__":
    asyncio.run(main())
