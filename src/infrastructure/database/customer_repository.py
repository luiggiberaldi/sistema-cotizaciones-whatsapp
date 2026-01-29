from typing import Optional, Dict
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class CustomerRepository:
    """Repositorio para gestionar clientes (tabla customers)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table = "customers"  # Nombre de la tabla migracion 008

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """Buscar cliente por teléfono."""
        try:
            response = self.supabase.table(self.table)\
                .select("*")\
                .eq("phone_number", phone)\
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
            # Campos obligatorios
            data = {
                "phone_number": phone,
                "full_name": name or "Cliente Desconocido"
            }
            
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
        """Actualizar nombre si no existe o cambiarlo."""
        try:
            response = self.supabase.table(self.table)\
                .update({"full_name": name})\
                .eq("phone_number", phone)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error actualizando nombre cliente {phone}: {e}")
            return None

    def update(self, customer_id: str, data: Dict) -> Optional[Dict]:
        """Actualizar datos del cliente por ID."""
        try:
            response = self.supabase.table(self.table)\
                .update(data)\
                .eq("id", customer_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error actualizando cliente {customer_id}: {e}")
            return None
