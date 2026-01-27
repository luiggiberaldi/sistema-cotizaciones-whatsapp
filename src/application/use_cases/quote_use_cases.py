"""
Casos de uso para Quote.
Contiene la lógica de aplicación para operaciones de cotizaciones.
"""
from typing import List, Optional
from ...domain.entities.quote import Quote, QuoteItem
from ...domain.repositories.quote_repository import QuoteRepository


class CreateQuoteUseCase:
    """Caso de uso para crear una cotización."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(self, quote: Quote) -> Quote:
        """
        Crear una nueva cotización.
        
        Args:
            quote: Cotización a crear
            
        Returns:
            Cotización creada con ID asignado
        """
        # Validar que el total sea correcto
        calculated_total = quote.calculate_total()
        if abs(quote.total - calculated_total) > 0.01:
            raise ValueError(f"El total no coincide: esperado {calculated_total}, recibido {quote.total}")
        
        return await self.repository.create(quote)


class GetQuoteUseCase:
    """Caso de uso para obtener una cotización por ID."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(self, quote_id: int) -> Optional[Quote]:
        """
        Obtener una cotización por su ID.
        
        Args:
            quote_id: ID de la cotización
            
        Returns:
            Cotización encontrada o None
        """
        return await self.repository.get_by_id(quote_id)


class ListQuotesUseCase:
    """Caso de uso para listar cotizaciones."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Quote]:
        """
        Listar cotizaciones con paginación y filtros.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros
            status: Filtrar por estado
            
        Returns:
            Lista de cotizaciones
        """
        if limit > 100:
            limit = 100  # Máximo 100 registros por página
        
        return await self.repository.get_all(skip, limit, status)


class UpdateQuoteUseCase:
    """Caso de uso para actualizar una cotización."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(self, quote_id: int, quote: Quote) -> Optional[Quote]:
        """
        Actualizar una cotización existente.
        
        Args:
            quote_id: ID de la cotización
            quote: Datos actualizados
            
        Returns:
            Cotización actualizada o None
        """
        # Verificar que la cotización existe
        existing = await self.repository.get_by_id(quote_id)
        if not existing:
            return None
        
        # Validar que el total sea correcto
        calculated_total = quote.calculate_total()
        if abs(quote.total - calculated_total) > 0.01:
            raise ValueError(f"El total no coincide: esperado {calculated_total}, recibido {quote.total}")
        
        return await self.repository.update(quote_id, quote)


class DeleteQuoteUseCase:
    """Caso de uso para eliminar una cotización."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(self, quote_id: int) -> bool:
        """
        Eliminar una cotización.
        
        Args:
            quote_id: ID de la cotización
            
        Returns:
            True si se eliminó, False si no existía
        """
        return await self.repository.delete(quote_id)


class GetQuotesByPhoneUseCase:
    """Caso de uso para obtener cotizaciones por teléfono del cliente."""
    
    def __init__(self, repository: QuoteRepository):
        self.repository = repository
    
    async def execute(self, client_phone: str) -> List[Quote]:
        """
        Obtener todas las cotizaciones de un cliente.
        
        Args:
            client_phone: Teléfono del cliente
            
        Returns:
            Lista de cotizaciones del cliente
        """
        return await self.repository.get_by_phone(client_phone)
