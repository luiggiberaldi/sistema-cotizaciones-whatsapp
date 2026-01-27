import asyncio
from supabase import create_client, Client

async def main():
    print("Intentando restablecer contrasena via Admin API...")
    
    # Hardcoded credentials (solo para este script de emergencia)
    SUPABASE_URL = "https://ikuliolpnpfitngurexm.supabase.co"
    SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlrdWxpb2xwbnBmaXRuZ3VyZXhtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTUzNjM1NiwiZXhwIjoyMDg1MTEyMzU2fQ.DbEoD6463wrgskjH5JHQL5EndG0zSQI29scsOM_RLyM"
    
    # Initialize Supabase with Service Key
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    email = "luiggiberaldi94@gmail.com"
    new_password = "password123"
    
    try:
        print(f"Buscando usuario {email}...")
        
        # List users
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
