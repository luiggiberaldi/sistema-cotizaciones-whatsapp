from typing import Optional, Union
from datetime import datetime
from pydantic import field_validator
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

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse datetime strings from Supabase"""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
