from typing import List, Dict, Optional, Union
from supabase import Client
import logging
from datetime import datetime
from ...domain.entities.product import Product

logger = logging.getLogger(__name__)

class ProductRepository:
    """Repositorio para manejar la persistencia de productos en Supabase."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table_name = "products"

    def _dict_to_product(self, data: Dict) -> Product:
        """Convertir diccionario DB a entidad Product."""
        # Manejar fechas si vienen como strings
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('updated_at') and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
        return Product(**data)

    def _product_to_dict(self, product: Product) -> Dict:
        """Convertir entidad Product a diccionario para DB."""
        data = product.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_none=True)
        # Asegurar que aliases sea lista (Postgres array)
        if 'aliases' not in data:
            data['aliases'] = []
        return data

    def get_all_products(self) -> List[Dict]:
        """
        Obtener todos los productos como diccionarios (Legacy para QuoteService).
        """
        try:
            response = self.supabase.table(self.table_name).select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error al obtener productos de Supabase: {e}")
            return []

    def get_all(self) -> List[Product]:
        """Obtener todos los productos como entidades."""
        data = self.get_all_products()
        return [self._dict_to_product(item) for item in data]

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Obtener producto por ID."""
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", product_id).execute()
            if response.data:
                return self._dict_to_product(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener producto {product_id}: {e}")
            return None

    def create(self, product: Product) -> Optional[Product]:
        """Crear producto."""
        try:
            data = self._product_to_dict(product)
            response = self.supabase.table(self.table_name).insert(data).execute()
            if response.data:
                return self._dict_to_product(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creando producto: {e}")
            raise e

    def update(self, product_id: str, product: Product) -> Optional[Product]:
        """Actualizar producto."""
        try:
            data = self._product_to_dict(product)
            data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table(self.table_name)\
                .update(data)\
                .eq("id", product_id)\
                .execute()
                
            if response.data:
                return self._dict_to_product(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error actualizando producto {product_id}: {e}")
            raise e

    def delete(self, product_id: str) -> bool:
        """Eliminar producto."""
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", product_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error eliminando producto {product_id}: {e}")
            return False
