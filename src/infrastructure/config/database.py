from supabase import create_client, Client
from .settings import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Obtener instancia única del cliente de Supabase."""
    global _supabase_client
    
    if _supabase_client is None:
        # Priorizar service_key para operaciones de backend (bypasses RLS)
        key = getattr(settings, 'supabase_service_key', settings.supabase_key)
        
        _supabase_client = create_client(
            settings.supabase_url, 
            key
        )
    
    return _supabase_client
