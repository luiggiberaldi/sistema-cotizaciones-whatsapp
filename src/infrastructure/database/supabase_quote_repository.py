"""
Adaptador de Supabase para el repositorio de Quote.
Implementa la interfaz QuoteRepository usando Supabase como backend.
"""
from typing import List, Optional
from datetime import datetime
from supabase import create_client, Client
from ...domain.entities.quote import Quote, QuoteItem, QuoteStatus
from ...domain.repositories.quote_repository import QuoteRepository
from ..config.settings import settings


class SupabaseQuoteRepository(QuoteRepository):
    """
    Implementación del repositorio de cotizaciones usando Supabase.
    """
    
    def __init__(self):
        """Inicializar cliente de Supabase."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        self.table_name = "quotes"
    
    def _dict_to_quote(self, data: dict) -> Quote:
        """Convertir diccionario de Supabase a entidad Quote."""
        # Convertir items de dict a QuoteItem
        items = [QuoteItem(**item) for item in data.get("items", [])]
        
        return Quote(
            id=data.get("id"),
            client_phone=data["client_phone"],
            items=items,
            total=float(data["total"]),
            status=QuoteStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else None,
            notes=data.get("notes"),
            customer_id=data.get("customer_id")
        )
    
    def _quote_to_dict(self, quote: Quote) -> dict:
        """Convertir entidad Quote a diccionario para Supabase."""
        data = {
            "client_phone": quote.client_phone,
            "items": [item.model_dump() for item in quote.items],
            "total": quote.total,
            "status": quote.status.value if hasattr(quote.status, 'value') else quote.status,
        }
        
        if quote.notes:
            data["notes"] = quote.notes
            
        if quote.customer_id:
            data["customer_id"] = quote.customer_id
        
        return data
    
    async def create(self, quote: Quote) -> Quote:
        """Crear una nueva cotización en Supabase."""
        data = self._quote_to_dict(quote)
        
        response = self.client.table(self.table_name).insert(data).execute()
        
        if not response.data:
            raise Exception("Error al crear la cotización")
        
        return self._dict_to_quote(response.data[0])
    
    async def get_by_id(self, quote_id: int) -> Optional[Quote]:
        """Obtener una cotización por su ID."""
        response = self.client.table(self.table_name).select("*").eq("id", quote_id).execute()
        
        if not response.data:
            return None
        
        return self._dict_to_quote(response.data[0])
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Quote]:
        """Obtener todas las cotizaciones con paginación y filtros."""
        query = self.client.table(self.table_name).select("*")
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).range(skip, skip + limit - 1)
        
        response = query.execute()
        
        return [self._dict_to_quote(item) for item in response.data]
    
    async def update(self, quote_id: int, quote: Quote) -> Optional[Quote]:
        """Actualizar una cotización existente."""
        data = self._quote_to_dict(quote)
        
        response = self.client.table(self.table_name).update(data).eq("id", quote_id).execute()
        
        if not response.data:
            return None
        
        return self._dict_to_quote(response.data[0])
    
    async def delete(self, quote_id: int) -> bool:
        """Eliminar una cotización."""
        response = self.client.table(self.table_name).delete().eq("id", quote_id).execute()
        
        return len(response.data) > 0
    
    async def get_by_phone(self, client_phone: str) -> List[Quote]:
        """Obtener todas las cotizaciones de un cliente por teléfono."""
        response = (
            self.client.table(self.table_name)
            .select("*")
            .eq("client_phone", client_phone)
            .order("created_at", desc=True)
            .execute()
        )
        
        return [self._dict_to_quote(item) for item in response.data]
