from typing import Optional, Dict
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class CustomerRepository:
    """Repositorio para gestionar clientes (tabla consumers)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table = "consumers"  # Nombre de la tabla en DB

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """Buscar cliente por teléfono."""
        try:
            response = self.supabase.table(self.table)\
                .select("*")\
                .eq("phone", phone)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error consultando cliente {phone}: {e}")
            return None

    def create(self, phone: str, name: str = None) -> Optional[Dict]:
        """Crear nuevo cliente."""
        try:
            data = {"phone": phone}
            if name:
                data["name"] = name
            
            response = self.supabase.table(self.table)\
                .insert(data)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creando cliente {phone}: {e}")
            return None
    
    def update_name(self, phone: str, name: str) -> Optional[Dict]:
        """Actualizar nombre si no existe."""
        try:
            response = self.supabase.table(self.table)\
                .update({"name": name})\
                .eq("phone", phone)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error actualizando nombre cliente {phone}: {e}")
            return None
