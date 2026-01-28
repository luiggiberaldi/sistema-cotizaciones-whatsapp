from typing import List, Dict, Optional
from datetime import datetime
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class SessionRepository:
    """Repositorio para manejar sesiones activas de usuarios en Supabase."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table_name = "active_sessions"

    def get_session(self, client_phone: str) -> Optional[Dict]:
        """
        Obtener sesión activa de un cliente.
        
        Args:
            client_phone: Número de teléfono del cliente
            
        Returns:
            Dict de la sesión con 'items' y 'updated_at' o None
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("client_phone", client_phone)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error al obtener sesión para {client_phone}: {e}")
            return None

    def create_or_update_session(self, client_phone: str, items: List[Dict]) -> Dict:
        """
        Crear o actualizar una sesión.
        
        Args:
            client_phone: Número de teléfono
            items: Lista de items acumulados
            
        Returns:
            Sesión actualizada
        """
        try:
            data = {
                "client_phone": client_phone,
                "items": items,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert (insert or update)
            response = self.supabase.table(self.table_name)\
                .upsert(data)\
                .execute()
                
            return response.data[0] if response.data else data
        except Exception as e:
            logger.error(f"Error al guardar sesión para {client_phone}: {e}")
            raise

    def delete_session(self, client_phone: str) -> bool:
        """
        Eliminar sesión (al finalizar compra o expirar).
        
        Args:
            client_phone: Número de teléfono
        """
        try:
            self.supabase.table(self.table_name)\
                .delete()\
                .eq("client_phone", client_phone)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error al eliminar sesión de {client_phone}: {e}")
            return False
