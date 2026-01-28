from typing import List, Dict, Optional
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class ProductRepository:
    """Repositorio para manejar la persistencia de productos en Supabase."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table_name = "products"

    def get_all_products(self) -> List[Dict]:
        """
        Obtener todos los productos del catálogo.
        
        Returns:
            Lista de productos como diccionarios.
        """
        try:
            response = self.supabase.table(self.table_name).select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error al obtener productos de Supabase: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Obtener un producto por su ID."""
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", product_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error al obtener producto {product_id}: {e}")
            return None
