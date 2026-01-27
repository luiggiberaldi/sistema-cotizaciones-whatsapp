"""
Schemas para generación de cotizaciones desde texto.
"""
from typing import Optional, List, Dict
from pydantic import Field
from src.domain.base import StrictBaseModel
from src.domain.entities.quote import QuoteStatus
from .quote_schemas import QuoteResponseSchema


class GenerateQuoteFromTextRequest(StrictBaseModel):
    """Schema para solicitud de generación de cotización desde texto."""
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Texto libre describiendo los productos (ej: 'Quiero 2 zapatos y 1 camisa')"
    )
    client_phone: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Teléfono del cliente"
    )
    fuzzy_threshold: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Umbral de similitud para fuzzy matching (0-100)"
    )
    status: QuoteStatus = Field(
        default=QuoteStatus.DRAFT,
        description="Estado inicial de la cotización"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas adicionales"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Quiero 2 zapatos y 1 camisa",
                "client_phone": "+58 412-1234567",
                "fuzzy_threshold": 70,
                "status": "draft",
                "notes": "Cliente VIP"
            }
        }
    }


class GenerateQuoteFromTextResponse(StrictBaseModel):
    """Schema para respuesta de generación de cotización."""
    
    quote: QuoteResponseSchema
    parsing_details: Optional[List[Dict]] = Field(
        None,
        description="Detalles del parsing (confianza, matches)"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "quote": {
                    "id": 1,
                    "client_phone": "+58 412-1234567",
                    "items": [
                        {
                            "product_name": "Zapatos",
                            "quantity": 2,
                            "unit_price": 45.99,
                            "subtotal": 91.98
                        }
                    ],
                    "total": 91.98,
                    "status": "draft",
                    "created_at": "2024-01-27T10:00:00Z",
                    "updated_at": "2024-01-27T10:00:00Z"
                },
                "parsing_details": [
                    {
                        "product": "Zapatos",
                        "matched_text": "zapatos",
                        "matched_to": "zapato",
                        "confidence": 95
                    }
                ]
            }
        }
    }


class ProductSearchRequest(StrictBaseModel):
    """Schema para búsqueda de productos."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Texto a buscar"
    )
    threshold: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Umbral de similitud"
    )
