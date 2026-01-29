from typing import Optional
from datetime import datetime
from ..base import StrictBaseModel

class BusinessInfo(StrictBaseModel):
    """
    Entidad que representa una configuración del negocio.
    """
    key: str
    value: str
    category: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
