"""
Entidad de dominio para Producto.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import Field
from ..base import StrictBaseModel

class Product(StrictBaseModel):
    """
    Entidad de dominio para Producto.
    """
    id: Optional[str] = Field(None, description="ID único del producto")
    name: str = Field(..., min_length=1, description="Nombre del producto")
    price: float = Field(..., gt=0, description="Precio unitario")
    category: Optional[str] = Field(None, description="Categoría del producto")
    image_url: Optional[str] = Field(None, description="URL de la imagen del producto")
    description: Optional[str] = Field(None, description="Descripción del producto")
    aliases: List[str] = Field(default_factory=list, description="Lista de alias para búsqueda")
    stock: Optional[int] = Field(None, ge=0, description="Stock disponible")
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
