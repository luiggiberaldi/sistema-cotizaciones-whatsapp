"""
Caso de uso para procesar mensajes de WhatsApp.
"""
import logging
from typing import Dict, Optional
from ...domain.services import QuoteService
from ...domain.repositories import QuoteRepository
from ...infrastructure.external import WhatsAppService, RetryQueue

logger = logging.getLogger(__name__)


class ProcessWhatsAppMessageUseCase:
    """
    Caso de uso para procesar mensajes de WhatsApp.
    
    Flujo:
    1. Recibir mensaje de WhatsApp
    2. Extraer texto del mensaje
    3. Generar cotización usando QuoteService
    4. Guardar cotización en Base de Datos
    5. Enviar respuesta automática
    6. Si falla el envío, agregar a cola de reintentos
    """
    
    def __init__(
        self,
        quote_service: QuoteService,
        quote_repository: QuoteRepository,
        whatsapp_service: WhatsAppService,
        retry_queue: RetryQueue
    ):
        """
        Inicializar caso de uso.
        
        Args:
            quote_service: Servicio de cotizaciones
            quote_repository: Repositorio de cotizaciones
            whatsapp_service: Servicio de WhatsApp
            retry_queue: Cola de reintentos
        """
        self.quote_service = quote_service
        self.quote_repository = quote_repository
        self.whatsapp_service = whatsapp_service
        self.retry_queue = retry_queue
    
    async def execute(self, message_data: Dict) -> Dict:
        """
        Procesar mensaje de WhatsApp.
        
        Args:
            message_data: Datos del mensaje (from, text, message_id, timestamp)
            
        Returns:
            Resultado del procesamiento
        """
        from_number = message_data.get('from')
        text = message_data.get('text', '')
        message_id = message_data.get('message_id')
        
        logger.info(f"Procesando mensaje de {from_number}: {text}")
        
        try:
            # Generar cotización desde texto
            result = self.quote_service.generate_quote_with_details(
                text=text,
                client_phone=f"+{from_number}",  # WhatsApp envía sin +
                fuzzy_threshold=70,
                notes=f"Generado desde WhatsApp (msg_id: {message_id})"
            )
            
            quote = result['quote']
            confidence_scores = result['confidence_scores']

            # Guardar en Base de Datos
            logger.info("Guardando cotización en base de datos...")
            logger.info(f"Tipo de quote: {type(quote)}")
            logger.info(f"Contenido de quote: {quote}")
            logger.info(f"Status type: {type(quote.status)}")
            
            created_quote = await self.quote_repository.create(quote)
            logger.info(f"Cotización guardada con ID: {created_quote.id}")
            
            # Preparar datos para enviar
            quote_data = {
                'items': [
                    {
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'subtotal': item.subtotal
                    }
                    for item in quote.items
                ],
                'total': quote.total
            }
            
            # Intentar enviar respuesta
            try:
                await self.whatsapp_service.send_quote_message(
                    to=from_number,
                    quote_data=quote_data
                )
                
                # Marcar mensaje como leído
                await self.whatsapp_service.mark_message_as_read(message_id)
                
                logger.info(f"Cotización enviada exitosamente a {from_number}")
                
                return {
                    'success': True,
                    'quote': quote_data,
                    'confidence_scores': confidence_scores,
                    'sent': True
                }
                
            except Exception as send_error:
                # Si falla el envío, agregar a cola de reintentos
                logger.error(f"Error enviando mensaje: {send_error}")
                
                message_text = self.whatsapp_service._format_quote_message(quote_data)
                
                self.retry_queue.add_message(
                    message_id=f"retry_{message_id}",
                    to=from_number,
                    message=message_text,
                    quote_data=quote_data,
                    max_attempts=5,
                    error=str(send_error)
                )
                
                return {
                    'success': True,
                    'quote': quote_data,
                    'confidence_scores': confidence_scores,
                    'sent': False,
                    'queued_for_retry': True,
                    'error': str(send_error)
                }
        
        except ValueError as e:
            # No se pudo generar cotización del texto
            logger.warning(f"No se pudo generar cotización: {e}")
            
            # Enviar mensaje de error al usuario
            error_message = (
                "❌ No pude entender tu solicitud.\n\n"
                "Por favor, intenta de nuevo con un formato como:\n"
                "\"Quiero 2 zapatos y 1 camisa\""
            )
            
            try:
                await self.whatsapp_service.send_message(
                    to=from_number,
                    message=error_message
                )
            except Exception as send_error:
                logger.error(f"Error enviando mensaje de error: {send_error}")
            
            return {
                'success': False,
                'error': str(e),
                'sent_error_message': True
            }
        
        except Exception as e:
            # Error inesperado
            logger.error(f"Error inesperado procesando mensaje: {e}", exc_info=True)
            
            return {
                'success': False,
                'error': str(e),
                'sent_error_message': False
            }


class RetryFailedMessagesUseCase:
    """
    Caso de uso para reintentar mensajes fallidos.
    
    Debe ejecutarse periódicamente (ej: cada minuto con un cron job).
    """
    
    def __init__(
        self,
        whatsapp_service: WhatsAppService,
        retry_queue: RetryQueue
    ):
        """
        Inicializar caso de uso.
        
        Args:
            whatsapp_service: Servicio de WhatsApp
            retry_queue: Cola de reintentos
        """
        self.whatsapp_service = whatsapp_service
        self.retry_queue = retry_queue
    
    async def execute(self) -> Dict:
        """
        Reintentar envío de mensajes fallidos.
        
        Returns:
            Estadísticas de reintentos
        """
        messages_to_retry = self.retry_queue.get_messages_to_retry()
        
        if not messages_to_retry:
            logger.info("No hay mensajes para reintentar")
            return {
                'messages_retried': 0,
                'successful': 0,
                'failed': 0
            }
        
        logger.info(f"Reintentando {len(messages_to_retry)} mensajes")
        
        successful = 0
        failed = 0
        
        for msg in messages_to_retry:
            try:
                # Intentar enviar
                if msg.quote_data:
                    await self.whatsapp_service.send_quote_message(
                        to=msg.to,
                        quote_data=msg.quote_data
                    )
                else:
                    await self.whatsapp_service.send_message(
                        to=msg.to,
                        message=msg.message
                    )
                
                # Actualizar como exitoso
                self.retry_queue.update_message_attempt(
                    message_id=msg.id,
                    success=True
                )
                
                successful += 1
                logger.info(f"Mensaje {msg.id} enviado exitosamente en reintento")
                
            except Exception as e:
                # Actualizar como fallido
                self.retry_queue.update_message_attempt(
                    message_id=msg.id,
                    success=False,
                    error=str(e)
                )
                
                failed += 1
                logger.error(f"Mensaje {msg.id} falló en reintento: {e}")
        
        return {
            'messages_retried': len(messages_to_retry),
            'successful': successful,
            'failed': failed
        }
