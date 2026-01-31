"""
Caso de uso para procesar mensajes de WhatsApp.
"""
import os
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from ...domain.services import QuoteService
from ...domain.repositories import QuoteRepository
from ...infrastructure.external import WhatsAppService, RetryQueue
from ...infrastructure.services.invoice_service import InvoiceService
from ...infrastructure.services.storage_service import StorageService
from ...infrastructure.database.customer_repository import CustomerRepository

logger = logging.getLogger(__name__)


class ProcessWhatsAppMessageUseCase:
    """
    Caso de uso para procesar mensajes de WhatsApp (Dispatcher).
    Delega la lógica a handlers especializados.
    """
    
    def __init__(
        self,
        quote_service: QuoteService,
        quote_repository: QuoteRepository,
        whatsapp_service: WhatsAppService,
        retry_queue: RetryQueue,
        session_repository: Optional['SessionRepository'] = None,
        invoice_service: Optional[InvoiceService] = None,
        storage_service: Optional[StorageService] = None,
        customer_repository: Optional[CustomerRepository] = None
    ):
        self.quote_service = quote_service
        self.whatsapp_service = whatsapp_service
        self.retry_queue = retry_queue
        self.customer_repository = customer_repository
        
        # Inicializar Handlers
        from ..handlers.whatsapp.greeting_handler import GreetingHandler
        from ..handlers.whatsapp.faq_handler import FAQHandler
        from ..handlers.whatsapp.catalog_handler import CatalogHandler
        from ..handlers.whatsapp.wizard_handler import WizardHandler
        from ..handlers.whatsapp.quote_handler import QuoteHandler
        from ..handlers.whatsapp.checkout_handler import CheckoutHandler
        
        # Servicios auxiliares (se pasan a los handlers que los necesiten)
        # Nota: Invoice y Storage se instancian on-demand o se pasan si ya existen
        inv_service = invoice_service or InvoiceService()
        sto_service = storage_service or StorageService()
        
        self.greeting_handler = GreetingHandler(whatsapp_service, quote_service, inv_service, sto_service)
        self.faq_handler = FAQHandler(whatsapp_service)
        self.catalog_handler = CatalogHandler(whatsapp_service, quote_service, inv_service, sto_service)
        self.wizard_handler = WizardHandler(whatsapp_service, session_repository)
        self.quote_handler = QuoteHandler(whatsapp_service, quote_service, session_repository)
        self.checkout_handler = CheckoutHandler(
            whatsapp_service, quote_service, quote_repository, 
            session_repository, inv_service, sto_service, customer_repository
        )
        
        # Para uso interno si es necesario
        self.session_repository = session_repository

    async def execute(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        try:
            return await self._execute_implementation(message_data)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            if from_number:
                try:
                    await self.whatsapp_service.send_message(
                        from_number,
                        "😓 Ocurrió un error técnico. Por favor intenta más tarde."
                    )
                except:
                    pass
            return {'success': False, 'error': str(e)}

    async def _execute_implementation(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        text = message_data.get('text', '').strip()
        message_id = message_data.get('message_id')
        sender_name = message_data.get('name')
        
        logger.info(f"Procesando mensaje de {from_number} ({sender_name or 'Desconocido'}): {text}")

        # --- Gestión de Clientes (CRM) ---
        customer = None
        if self.customer_repository:
            from ...infrastructure.services.customer_service import CustomerService
            c_service = CustomerService(self.customer_repository)
            customer = c_service.get_customer_by_phone(from_number)
            if customer:
                logger.info(f"Cliente identificado: {customer.get('full_name')} ({customer.get('id')})")
        
        # Contexto para handlers
        message_data['customer'] = customer
        text_lower = text.lower()

        # 1. INTENCIONES PRIORITARIAS
        
        # A. Vaciar Carrito
        empty_cart_keywords = ['vacia', 'vaciar', 'limpiar carrito', 'borrar todo', 'eliminar todo', 'vacía', 'vacíar', 'cancelar pedido']
        if any(keyword in text_lower for keyword in empty_cart_keywords):
             if self.session_repository:
                 self.session_repository.delete_session(from_number)
             await self.whatsapp_service.send_message(from_number, "🗑️ Tu carrito ha sido vaciado. ¿Qué te gustaría pedir ahora?")
             return {'success': True, 'action': 'empty_cart'}

        # B. Saludo
        greeting_keywords = ['hola', 'buen', 'buenas', 'que tal', 'hey', 'hello', 'hi', 'saludos']
        if any(keyword in text_lower for keyword in greeting_keywords) and len(text.split()) < 5:
            return await self.greeting_handler.handle(message_data)

        # C. FAQs (Ubicación, Delivery, Pago)
        location_keywords = ['ubicacion', 'donde', 'direccion', 'local', 'tienda', 'ubicados', 'horario', 'hora', 'abierto']
        if any(keyword in text_lower for keyword in location_keywords):
            message_data['intent'] = 'location'
            return await self.faq_handler.handle(message_data)
            
        delivery_keywords = ['delivery', 'envio', 'domicilio', 'traer', 'llevan', 'zonas', 'costo de envio']
        if any(keyword in text_lower for keyword in delivery_keywords):
            message_data['intent'] = 'delivery'
            return await self.faq_handler.handle(message_data)
            
        payment_keywords = ['pagar', 'pago', 'cuenta', 'zelle', 'binance', 'banco', 'transferencia', 'pago movil', 'bolivares', 'dolares', 'metodos', 'como pago']
        if any(keyword in text_lower for keyword in payment_keywords):
             message_data['intent'] = 'payment'
             return await self.faq_handler.handle(message_data)

        # D. Catálogo
        catalog_keywords = ['catalogo', 'catálogo', 'lista de precios', 'ver productos', 'precio de todo']
        if any(keyword in text_lower for keyword in catalog_keywords):
            return await self.catalog_handler.handle(message_data)

        # 2. GESTIÓN DE WIZARD (Si estamos en medio de una conversa de datos)
        if self.session_repository:
            session = self.session_repository.get_session(from_number)
            if session and session.get('conversation_step', 'shopping') != 'shopping':
                result = await self.wizard_handler.handle(message_data)
                
                # Si el wizard indica que se confirmó el checkout
                if result.get('action') == 'trigger_checkout':
                    return await self.checkout_handler.handle(message_data)
                
                return result

        # 3. CHECKOUT (Confirmación)
        checkout_keywords = ['confirmar', 'listo', 'finalizar', 'comprar', 'fin', 'total']
        if any(keyword in text_lower for keyword in checkout_keywords):
            # Verificación de Cliente (Wizard Trigger)
            # Solo permitir checkout directo si ya tenemos datos del cliente (DB o Sesión)
            
            client_fully_identified = False
            
            # 1. ¿Está en CRM y tiene datos COMPLETOS?
            if message_data.get('customer'):
                cust = message_data['customer']
                # Validar que tenga datos reales y no sea un placeholder
                name = cust.get('full_name', '')
                has_valid_name = name and len(name) > 2 and "Desconocido" not in name
                has_dni = bool(cust.get('dni_rif'))
                has_address = bool(cust.get('main_address'))
                
                if has_valid_name and has_dni and has_address:
                    client_fully_identified = True
                    logger.info(f"Cliente identificado y completo: {name}")
                else:
                    logger.info(f"Cliente en BD pero incompleto: Name={has_valid_name}, DNI={has_dni}, Addr={has_address}")
            
            # 2. ¿Tiene datos en Sesión temporal?
            elif self.session_repository:
                session = self.session_repository.get_session(from_number)
                if session and session.get('client_data') and session['client_data'].get('name'):
                     client_fully_identified = True
            
            # Si NO está identificado, iniciar Wizard
            if not client_fully_identified:
                logger.info(f"Cliente {from_number} no identificado. Iniciando Wizard de registro.")
                if self.session_repository:
                    # Validar que tenga items antes de pedir datos
                    session = self.session_repository.get_session(from_number)
                    if not session or not session.get('items'):
                         # Dejar que checkout handler maneje el error de "carrito vacío"
                         return await self.checkout_handler.handle(message_data)
                    
                    # Iniciar Wizard
                    self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_NAME')
                    await self.whatsapp_service.send_message(
                        from_number, 
                        "📝 Para generar tu recibo formal, necesito unos breves datos.\n\n¿Cuál es tu **Nombre y Apellido**?"
                    )
                    return {'success': True, 'action': 'start_registration_wizard'}

            return await self.checkout_handler.handle(message_data)

        # 4. COTIZACIÓN / AGREGAR ITEMS (Default)
        # Detectar intención de cotizar
        quote_keywords = ['cotiz', 'precio', 'cuanto', 'quiero', 'necesito', 'tienes', 'dame', 'busca', 'valor', 'costo']
        is_quote_intent = any(keyword in text_lower for keyword in quote_keywords)
        
        # Pasar flag al handler
        message_data['is_quote_intent'] = is_quote_intent
        
        # Llamar al QuoteHandler que gestionará parsing o fallback
        return await self.quote_handler.handle(message_data)


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
