"""
Schemas de API (DTOs) para Quote.
Define los modelos de entrada/salida de la API REST.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from src.domain.base import StrictBaseModel
from src.domain.entities.quote import QuoteStatus


class QuoteItemSchema(StrictBaseModel):
    """Schema para item de cotización."""
    
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    subtotal: float = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=500)


class QuoteCreateSchema(StrictBaseModel):
    """Schema para crear una cotización."""
    
    client_phone: str = Field(..., min_length=7, max_length=20)
    items: List[QuoteItemSchema] = Field(..., min_length=1)
    total: float = Field(..., ge=0)
    status: QuoteStatus = Field(default=QuoteStatus.DRAFT)
    notes: Optional[str] = Field(None, max_length=1000)


class QuoteUpdateSchema(StrictBaseModel):
    """Schema para actualizar una cotización."""
    
    client_phone: Optional[str] = Field(None, min_length=7, max_length=20)
    items: Optional[List[QuoteItemSchema]] = Field(None, min_length=1)
    total: Optional[float] = Field(None, ge=0)
    status: Optional[QuoteStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class QuoteResponseSchema(StrictBaseModel):
    """Schema para respuesta de cotización."""
    
    id: int
    client_phone: str
    items: List[QuoteItemSchema]
    total: float
    status: QuoteStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "client_phone": "+58 412-1234567",
                "items": [
                    {
                        "product_name": "Laptop Dell XPS 15",
                        "quantity": 1,
                        "unit_price": 1200.00,
                        "subtotal": 1200.00,
                        "description": "Laptop de alto rendimiento"
                    }
                ],
                "total": 1200.00,
                "status": "pending",
                "notes": "Cliente VIP",
                "created_at": "2024-01-27T10:00:00Z",
                "updated_at": "2024-01-27T10:00:00Z"
            }
        }
    }


class QuoteListResponseSchema(StrictBaseModel):
    """Schema para lista de cotizaciones."""
    
    quotes: List[QuoteResponseSchema]
    total: int
    skip: int
    limit: int
