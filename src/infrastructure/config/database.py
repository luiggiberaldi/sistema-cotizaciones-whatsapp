from supabase import create_client, Client
from .settings import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Obtener instancia única del cliente de Supabase."""
    global _supabase_client
    
    if _supabase_client is None:
        # Priorizar service_key para operaciones de backend (bypasses RLS)
        # Intentar obtener de settings, luego de os.environ directamente
        service_key = getattr(settings, 'supabase_service_key', None)
        if not service_key:
            import os
            service_key = os.getenv('SUPABASE_SERVICE_KEY')
            
        key = service_key if service_key else settings.supabase_key
        
        if not key:
            raise ValueError("No SUPABASE_KEY or SUPABASE_SERVICE_KEY found in settings")

        _supabase_client = create_client(
            settings.supabase_url, 
            key
        )
    
    return _supabase_client
