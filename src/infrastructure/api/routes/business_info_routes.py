from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from ....domain.entities.business_info import BusinessInfo
from ...services.business_info_service import BusinessInfoService
from ..dependencies import get_current_active_user

router = APIRouter(
    prefix="/business-info",
    tags=["business-info"]
)

# Instancia global del servicio (podría inyectarse)
business_info_service = BusinessInfoService()

@router.get("/", response_model=List[BusinessInfo])
async def get_all_business_info(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Obtener toda la información del negocio.
    """
    try:
        return business_info_service.get_all_info()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo información del negocio: {str(e)}"
        )

@router.put("/", response_model=List[BusinessInfo])
async def update_business_info(
    updates: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_active_user)
):
    """
    Actualizar información del negocio.
    
    Espera una lista de objetos con 'key' y los campos a actualizar ('value', 'is_active', etc).
    """
    try:
        return business_info_service.update_info(updates)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando información del negocio: {str(e)}"
        )
