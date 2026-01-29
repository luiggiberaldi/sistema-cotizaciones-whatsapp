"""
Endpoints para envío masivo de mensajes (Broadcast).
"""
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, status
import httpx
from pydantic import BaseModel, Field
from datetime import datetime
from ...external import WhatsAppService
from ...database.supabase_quote_repository import SupabaseQuoteRepository
from ....domain.base import StrictBaseModel

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/broadcast", tags=["broadcast"])

# Inicializar servicios
# Inicializar servicios
whatsapp_service = WhatsAppService()
# El repositorio se inicializa dentro del endpoint para evitar problemas de contexto


class ClientInfo(StrictBaseModel):
    """Información del cliente para broadcast."""
    phone: str = Field(..., description="Número de teléfono del cliente")
    name: str = Field(..., description="Nombre del cliente")
    quote_id: Optional[int] = Field(None, description="ID de cotización asociada")


class BroadcastTemplateRequest(StrictBaseModel):
    """Request para envío de template a múltiples clientes."""
    clients: List[ClientInfo] = Field(..., min_length=1, description="Lista de clientes")
    template_name: str = Field(..., description="Nombre del template aprobado por Meta")
    language_code: str = Field(default="es", description="Código de idioma")
    parameters: List[str] = Field(default=[], description="Parámetros del template")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "clients": [
                    {"phone": "+58 412-1234567", "name": "Cliente 1", "quote_id": 1},
                    {"phone": "+58 424-9876543", "name": "Cliente 2", "quote_id": 2}
                ],
                "template_name": "hello_world",
                "language_code": "es",
                "parameters": []
            }
        }
    }


class BroadcastResult(StrictBaseModel):
    """Resultado del envío a un cliente."""
    phone: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class BroadcastResponse(StrictBaseModel):
    """Respuesta del broadcast."""
    status: str
    total_clients: int
    successful: int
    failed: int
    results: List[BroadcastResult]


@router.post(
    "/send-template",
    response_model=BroadcastResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar template a múltiples clientes",
    description="Envía un mensaje plantilla aprobado por Meta a una lista de clientes"
)
async def send_template_broadcast(request: BroadcastTemplateRequest):
    """
    Enviar mensaje plantilla a múltiples clientes.
    
    Este endpoint permite enviar mensajes plantilla (templates) aprobados por Meta
    a una lista de clientes de forma masiva.
    
    **Requisitos**:
    - Template debe estar aprobado en Meta Business Manager
    - Números de teléfono en formato internacional
    - Parámetros deben coincidir con el template
    
    **Ejemplos de templates**:
    - `hello_world`: Template simple sin parámetros
    - `quote_notification`: Notificación de cotización con parámetros
    - `payment_reminder`: Recordatorio de pago
    """
    results = []
    successful = 0
    failed = 0
    
    logger.info(
        f"Iniciando broadcast a {len(request.clients)} clientes "
        f"con template '{request.template_name}'"
    )
    
    # Inicializar repositorio localmente
    quote_repo = SupabaseQuoteRepository()
    
    for client in request.clients:
        try:
            # Limpiar número de teléfono (remover + y espacios)
            phone = client.phone.replace('+', '').replace(' ', '').replace('-', '')
            
            # Reemplazar parámetros dinámicos
            final_params = []
            for p in request.parameters:
                if p == '{{name}}':
                    final_params.append(client.name)
                elif p == '{{total}}':
                    total_str = "$0.00"
                    try:
                        if client.quote_id:
                            # Prioridad 1: Usar ID específico
                            quote = await quote_repo.get_by_id(client.quote_id)
                            if quote:
                                total_str = f"${quote.total:.2f}"
                        else:
                            # Prioridad 2: Buscar última cotización por teléfono
                            user_quotes = await quote_repo.get_by_phone(phone)
                            if user_quotes:
                                total_str = f"${user_quotes[0].total:.2f}"
                    except Exception as e:
                        logger.warning(f"No se pudo obtener el total para {phone}: {e}")
                    
                    final_params.append(total_str)
                elif p == '{{fecha}}':
                    final_params.append(datetime.now().strftime("%d/%m/%Y"))
                else:
                    final_params.append(p)

            # Enviar template
            response = await whatsapp_service.send_template_message(
                to=phone,
                template_name=request.template_name,
                language_code=request.language_code,
                parameters=final_params
            )
            
            # Extraer message_id de la respuesta
            message_id = response.get('messages', [{}])[0].get('id')
            
            results.append(BroadcastResult(
                phone=client.phone,
                success=True,
                message_id=message_id
            ))
            
            successful += 1
            logger.info(f"Template enviado exitosamente a {client.phone}")
            
        except httpx.HTTPStatusError as e:
            # Capturar detalles específicos de la API de WhatsApp/Meta
            error_detail = str(e)
            try:
                error_body = e.response.json()
                if 'error' in error_body:
                    error_detail = error_body['error'].get('message', str(e))
                else:
                    error_detail = f"Status {e.response.status_code}: {e.response.text}"
            except Exception:
                pass
                
            logger.error(f"Error de API Meta para {client.phone}: {error_detail}")
            
            results.append(BroadcastResult(
                phone=client.phone,
                success=False,
                error=error_detail
            ))
            failed += 1
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error inesperado enviando template a {client.phone}: {error_msg}")
            
            results.append(BroadcastResult(
                phone=client.phone,
                success=False,
                error=error_msg
            ))
            
            failed += 1
    
    logger.info(
        f"Broadcast completado: {successful} exitosos, {failed} fallidos"
    )
    
    return BroadcastResponse(
        status="completed",
        total_clients=len(request.clients),
        successful=successful,
        failed=failed,
        results=results
    )


@router.get(
    "/templates",
    summary="Listar templates disponibles",
    description="Obtiene la lista de templates configurados (hardcoded por ahora)"
)
async def get_available_templates():
    """
    Obtener lista de templates disponibles.
    
    Por ahora retorna una lista hardcoded de templates comunes.
    En el futuro, esto podría consultar la API de Meta.
    """
    templates = [
        {
            "name": "hello_world",
            "description": "Template simple de saludo",
            "language": "es",
            "parameters": []
        },
        {
            "name": "quote_notification",
            "description": "Notificación de cotización generada",
            "language": "es",
            "parameters": ["nombre_cliente", "total"]
        },
        {
            "name": "payment_reminder",
            "description": "Recordatorio de pago pendiente",
            "language": "es",
            "parameters": ["nombre_cliente", "monto", "fecha_vencimiento"]
        }
    ]
    
    return {
        "status": "ok",
        "templates": templates
    }
