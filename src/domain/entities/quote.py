"""
Entidad de dominio para Quote (Cotización).
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import Field, field_validator, model_validator
from ..base import StrictBaseModel


class QuoteStatus(str, Enum):
    """Estados posibles de una cotización."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class QuoteItem(StrictBaseModel):
    """Item individual de una cotización."""
    
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del producto o servicio"
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Cantidad del producto"
    )
    unit_price: float = Field(
        ...,
        gt=0,
        description="Precio unitario"
    )
    subtotal: float = Field(
        ...,
        ge=0,
        description="Subtotal del item (cantidad * precio unitario)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción adicional del item"
    )
    
    @model_validator(mode='after')
    def validate_subtotal(self):
        """Validar que el subtotal sea correcto."""
        expected_subtotal = round(self.quantity * self.unit_price, 2)
        if abs(self.subtotal - expected_subtotal) > 0.01:
            raise ValueError(
                f"El subtotal {self.subtotal} no coincide con "
                f"cantidad * precio unitario = {expected_subtotal}"
            )
        return self


class Quote(StrictBaseModel):
    """
    Entidad de dominio para Cotización.
    
    Representa una cotización con todos sus detalles y validaciones.
    """
    
    id: Optional[int] = Field(
        None,
        description="ID autoincremental (correlativo) generado por la base de datos"
    )
    client_phone: str = Field(
        ...,
        min_length=7,
        max_length=20,
        pattern=r'^\+?[0-9\s\-\(\)]+$',
        description="Teléfono del cliente (formato internacional permitido)"
    )
    items: List[QuoteItem] = Field(
        ...,
        min_length=1,
        description="Lista de items de la cotización (mínimo 1)"
    )
    total: float = Field(
        ...,
        ge=0,
        description="Total de la cotización"
    )
    status: QuoteStatus = Field(
        default=QuoteStatus.DRAFT,
        description="Estado de la cotización"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Fecha y hora de creación"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Fecha y hora de última actualización"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas adicionales sobre la cotización"
    )
    customer_id: Optional[str] = Field(
        None,
        description="ID del cliente asociado (UUID)"
    )
    
    @field_validator('client_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validar y limpiar el número de teléfono."""
        # Eliminar espacios en blanco adicionales
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("El teléfono no puede estar vacío")
        return cleaned
    
    @model_validator(mode='after')
    def validate_total(self):
        """Validar que el total sea correcto."""
        expected_total = round(sum(item.subtotal for item in self.items), 2)
        if abs(self.total - expected_total) > 0.01:
            raise ValueError(
                f"El total {self.total} no coincide con "
                f"la suma de subtotales = {expected_total}"
            )
        return self
    
    def calculate_total(self) -> float:
        """Calcular el total de la cotización."""
        return round(sum(item.subtotal for item in self.items), 2)
    
    def add_item(self, item: QuoteItem) -> None:
        """Agregar un item a la cotización y recalcular el total."""
        self.items.append(item)
        self.total = self.calculate_total()
    
    def remove_item(self, index: int) -> None:
        """Remover un item de la cotización y recalcular el total."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.total = self.calculate_total()
        else:
            raise IndexError("Índice de item inválido")
