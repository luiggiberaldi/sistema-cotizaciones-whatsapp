"""
Repositorio abstracto para Quote (Puerto).
Define el contrato que deben implementar los adaptadores de persistencia.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.quote import Quote


class QuoteRepository(ABC):
    """
    Interfaz del repositorio de cotizaciones.
    
    Define las operaciones de persistencia que deben ser implementadas
    por los adaptadores de infraestructura (Supabase, PostgreSQL, etc.).
    """
    
    @abstractmethod
    async def create(self, quote: Quote) -> Quote:
        """
        Crear una nueva cotización.
        
        Args:
            quote: Cotización a crear (sin ID)
            
        Returns:
            Cotización creada con ID asignado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, quote_id: int) -> Optional[Quote]:
        """
        Obtener una cotización por su ID.
        
        Args:
            quote_id: ID de la cotización
            
        Returns:
            Cotización encontrada o None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Quote]:
        """
        Obtener todas las cotizaciones con paginación y filtros.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            status: Filtrar por estado (opcional)
            
        Returns:
            Lista de cotizaciones
        """
        pass
    
    @abstractmethod
    async def update(self, quote_id: int, quote: Quote) -> Optional[Quote]:
        """
        Actualizar una cotización existente.
        
        Args:
            quote_id: ID de la cotización a actualizar
            quote: Datos actualizados de la cotización
            
        Returns:
            Cotización actualizada o None si no existe
        """
        pass
    
    @abstractmethod
    async def delete(self, quote_id: int) -> bool:
        """
        Eliminar una cotización.
        
        Args:
            quote_id: ID de la cotización a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        pass
    
    @abstractmethod
    async def get_by_phone(self, client_phone: str) -> List[Quote]:
        """
        Obtener todas las cotizaciones de un cliente por teléfono.
        
        Args:
            client_phone: Teléfono del cliente
            
        Returns:
            Lista de cotizaciones del cliente
        """
        pass
