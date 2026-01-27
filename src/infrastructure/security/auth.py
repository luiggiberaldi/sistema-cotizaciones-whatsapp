from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from ..config.settings import settings

# Definir el esquema de seguridad Bearer
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verifica el token JWT utilizando el cliente oficial de Supabase.
    Este método es más seguro y soporta automáticamente el cambio de algoritmos de firma.
    """
    token = credentials.credentials
    
    # Inicializamos el cliente de Supabase para la validación
    # (settings.supabase_url y settings.supabase_key deben estar en tu .env)
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    
    try:
        # El cliente valida la firma, la expiración y el emisor (Supabase)
        user_response = supabase.auth.get_user(token)
        
        if not user_response.user:
            raise Exception("Usuario no encontrado en la respuesta de Supabase")
            
        # Retornamos el payload del usuario para que esté disponible en las rutas
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "aud": user_response.user.aud
        }
        
    except Exception as e:
        # Log para depuración interna del servidor
        print(f"Error de Autenticación: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu sesión ha expirado o es inválida. Por favor, inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
