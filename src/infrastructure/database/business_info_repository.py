from typing import List, Optional, Dict
from supabase import Client
from ..config.database import get_supabase_client
from ...domain.entities.business_info import BusinessInfo

class BusinessInfoRepository:
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        self.table = "business_info"

    def get_all(self) -> List[BusinessInfo]:
        """Obtener toda la información activa del negocio."""
        response = self.client.table(self.table)\
            .select("*")\
            .eq("is_active", True)\
            .execute()
            
        return [BusinessInfo(**item) for item in response.data]

    def get_by_category(self, category: str) -> List[BusinessInfo]:
        """Obtener información por categoría."""
        response = self.client.table(self.table)\
            .select("*")\
            .eq("category", category)\
            .eq("is_active", True)\
            .execute()
            
        return [BusinessInfo(**item) for item in response.data]

    def update(self, key: str, value: str) -> Optional[BusinessInfo]:
        """Actualizar un valor por su clave."""
        response = self.client.table(self.table)\
            .update({"value": value, "updated_at": "now()"})\
            .eq("key", key)\
            .execute()
            
        if response.data:
            return BusinessInfo(**response.data[0])
        return None

    def update_bulk(self, updates: List[Dict]) -> List[BusinessInfo]:
        """Actualizar múltiples valores."""
        # Supabase upsert or loop updates. Since we only update values, loop might be safer/easier 
        # unless we use upsert with specific columns.
        results = []
        for item in updates:
            # We assume item has 'key' and 'value' and maybe 'is_active'
            key = item.get('key')
            data = {k: v for k, v in item.items() if k != 'key'}
            data['updated_at'] = "now()"
            
            if key:
                response = self.client.table(self.table)\
                    .update(data)\
                    .eq("key", key)\
                    .execute()
                if response.data:
                    results.append(BusinessInfo(**response.data[0]))
        return results
