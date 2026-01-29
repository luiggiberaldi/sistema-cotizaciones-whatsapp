"""
Endpoints para webhook de WhatsApp Cloud API.
"""
import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, Request, Query, status
from ....domain.services import QuoteService
from ....infrastructure.external import WhatsAppService, RetryQueue
from ....application.use_cases import (
    ProcessWhatsAppMessageUseCase,
    RetryFailedMessagesUseCase
)
from ....infrastructure.config.database import get_supabase_client
from ....infrastructure.database.product_repository import ProductRepository
from ....infrastructure.database import SupabaseQuoteRepository

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/webhook", tags=["webhook"])
from ....infrastructure.database.customer_repository import CustomerRepository
from ....infrastructure.database.session_repository import SessionRepository
from ....infrastructure.services.invoice_service import InvoiceService
from ....infrastructure.services.storage_service import StorageService

# Inicializar servicios
supabase = get_supabase_client()
product_repository = ProductRepository(supabase)
quote_service = QuoteService(product_repository)
quote_repository = SupabaseQuoteRepository()
session_repository = SessionRepository(supabase)
customer_repository = CustomerRepository(supabase)
invoice_service = InvoiceService()
storage_service = StorageService(supabase)
whatsapp_service = WhatsAppService()
retry_queue = RetryQueue()

# Inicializar casos de uso
process_message_use_case = ProcessWhatsAppMessageUseCase(
    quote_service=quote_service,
    quote_repository=quote_repository,
    whatsapp_service=whatsapp_service,
    retry_queue=retry_queue,
    session_repository=session_repository,
    invoice_service=invoice_service,
    storage_service=storage_service,
    customer_repository=customer_repository
)

retry_messages_use_case = RetryFailedMessagesUseCase(
    whatsapp_service=whatsapp_service,
    retry_queue=retry_queue
)


@router.get(
    "",
    summary="Verificar webhook de WhatsApp",
    description="Endpoint de verificación para WhatsApp Cloud API"
)
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")
):
    """
    Verificar webhook de WhatsApp.
    
    Meta envía una petición GET con parámetros de verificación.
    Debemos retornar el challenge si el token es válido.
    
    Documentación: https://developers.facebook.com/docs/graph-api/webhooks/getting-started
    """
    logger.info(f"Verificación de webhook: mode={mode}, token={token[:10]}...")
    
    # Verificar token
    challenge_response = whatsapp_service.verify_webhook(mode, token, challenge)
    
    if challenge_response:
        logger.info("Webhook verificado exitosamente")
        return int(challenge_response)
    
    logger.warning("Verificación de webhook fallida")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Token de verificación inválido"
    )


@router.post(
    "",
    summary="Recibir mensajes de WhatsApp",
    description="Webhook para recibir mensajes de WhatsApp Cloud API"
)
async def receive_webhook(request: Request):
    """
    Recibir mensajes de WhatsApp.
    
    Meta envía una petición POST cuando hay un nuevo mensaje.
    
    Flujo:
    1. Extraer datos del mensaje
    2. Generar cotización usando QuoteService
    3. Enviar respuesta automática
    4. Si falla, agregar a cola de reintentos
    """
    try:
        # Obtener datos del webhook
        webhook_data = await request.json()
        
        logger.info(f"Webhook recibido: {webhook_data}")
        
        # Extraer datos del mensaje
        message_data = whatsapp_service.extract_message_data(webhook_data)
        
        if not message_data:
            logger.info("Webhook no contiene mensaje de texto válido")
            return {"status": "ok", "message": "No message to process"}
        
        # Procesar mensaje
        result = await process_message_use_case.execute(message_data)
        
        return {
            "status": "ok",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}", exc_info=True)
        
        # Retornar 200 para que Meta no reintente
        # (nosotros manejamos los reintentos internamente)
        return {
            "status": "error",
            "error": str(e)
        }


@router.post(
    "/retry",
    summary="Reintentar mensajes fallidos",
    description="Endpoint para reintentar manualmente mensajes en cola"
)
async def retry_failed_messages():
    """
    Reintentar mensajes fallidos.
    
    Este endpoint puede ser llamado manualmente o por un cron job.
    """
    try:
        result = await retry_messages_use_case.execute()
        
        return {
            "status": "ok",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error reintentando mensajes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reintentando mensajes: {str(e)}"
        )


@router.get(
    "/queue-status",
    summary="Estado de la cola de reintentos",
    description="Obtener información sobre la cola de reintentos"
)
async def get_queue_status():
    """Obtener estado de la cola de reintentos."""
    try:
        queue_size = retry_queue.get_queue_size()
        messages_to_retry = retry_queue.get_messages_to_retry()
        failed_messages = retry_queue.get_failed_messages()
        
        return {
            "queue_size": queue_size,
            "pending_retry": len(messages_to_retry),
            "failed": len(failed_messages),
            "failed_messages": [
                {
                    "id": msg.id,
                    "to": msg.to,
                    "attempts": msg.attempts,
                    "last_error": msg.last_error
                }
                for msg in failed_messages
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cola: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado: {str(e)}"
        )
