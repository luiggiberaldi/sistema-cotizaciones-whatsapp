from typing import Optional, Dict, List
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

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Obtener lista de clientes paginada."""
        try:
            response = self.supabase.table(self.table)\
                .select("*")\
                .range(skip, skip + limit - 1)\
                .order("created_at", desc=True)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error listando clientes: {e}")
            return []
    def delete(self, customer_id: str) -> bool:
        """Eliminar cliente si no tiene cotizaciones."""
        try:
            # 1. Verificar integridad (Check quotes)
            # Nota: Usamos select count para eficiencia
            quotes_check = self.supabase.table("quotes")\
                .select("id", count="exact")\
                .eq("customer_id", customer_id)\
                .execute()
            
            # La propiedad count viene en el response
            if quotes_check.count and quotes_check.count > 0:
                raise ValueError("No se puede eliminar el cliente porque tiene cotizaciones registradas.")
            
            # 2. Eliminar
            response = self.supabase.table(self.table)\
                .delete()\
                .eq("id", customer_id)\
                .execute()
            
            return len(response.data) > 0
        except ValueError as ve:
            # Re-lanzar errores de validación para manejarlos en el router
            raise ve
        except Exception as e:
            logger.error(f"Error eliminando cliente {customer_id}: {e}")
            raise e
    def get_filtered(self, query: Optional[str] = None, quote_status: Optional[str] = None) -> List[Dict]:
        """
        Obtener clientes filtrados por nombre/teléfono y/o estado de sus cotizaciones.
        """
        try:
            # Iniciamos la consulta base
            # Si filtramos por status de cotización, necesitamos un join (quotes!inner)
            if quote_status:
                builder = self.supabase.table(self.table)\
                    .select("*, quotes!inner(status)")\
                    .eq("quotes.status", quote_status)
            else:
                builder = self.supabase.table(self.table).select("*")

            # Filtro de búsqueda (OR entre nombre y teléfono)
            if query:
                # Supabase sintaxis para OR: "column1.ilike.%val%,column2.ilike.%val%"
                search_filter = f"full_name.ilike.%{query}%,phone_number.ilike.%{query}%"
                builder = builder.or_(search_filter)

            response = builder.order("full_name").execute()
            
            # Limpiar duplicados si el join trajo varias filas por cliente con múltiples cotizaciones
            unique_customers = {}
            for item in response.data:
                cid = item['id']
                if cid not in unique_customers:
                    # Remover el campo joined 'quotes' de la respuesta final para limpieza
                    if 'quotes' in item: del item['quotes']
                    unique_customers[cid] = item
            
            return list(unique_customers.values())
        except Exception as e:
            logger.error(f"Error filtrando clientes (q={query}, s={quote_status}): {e}")
            return []
