from supabase import create_client, Client
from .settings import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Obtener instancia única del cliente de Supabase."""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url, 
            settings.supabase_key
        )
    
    return _supabase_client
