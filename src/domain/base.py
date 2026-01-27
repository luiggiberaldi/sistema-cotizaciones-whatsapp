"""
Módulo de configuración de Pydantic con validación estricta.
"""
from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """
    Modelo base con configuración estricta de Pydantic.
    
    Configuración:
    - strict=True: Validación estricta de tipos (no conversiones automáticas)
    - validate_assignment=True: Validar al asignar valores después de la creación
    - arbitrary_types_allowed=False: No permitir tipos arbitrarios
    - str_strip_whitespace=True: Eliminar espacios en blanco de strings
    - validate_default=True: Validar valores por defecto
    - use_enum_values=True: Usar valores de enums en lugar de instancias
    """
    
    model_config = ConfigDict(
        strict=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
        frozen=False,  # Permitir mutabilidad (cambiar a True para inmutabilidad)
        extra='forbid',  # Prohibir campos extra no definidos
    )
