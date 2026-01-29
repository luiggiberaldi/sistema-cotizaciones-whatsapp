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
        retry_queue: RetryQueue,
        session_repository: Optional['SessionRepository'] = None,
        invoice_service: Optional[InvoiceService] = None,
        storage_service: Optional[StorageService] = None,
        customer_repository: Optional[CustomerRepository] = None
    ):
        self.quote_service = quote_service
        self.quote_repository = quote_repository
        self.whatsapp_service = whatsapp_service
        self.retry_queue = retry_queue
        self.session_repository = session_repository
        self.invoice_service = invoice_service or InvoiceService()
        self.storage_service = storage_service or StorageService()
        self.customer_repository = customer_repository

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

        # --- Gestión de Clientes ---
        customer = None
        if self.customer_repository:
            # Buscar cliente existente
            customer = self.customer_repository.get_by_phone(from_number)
            
            if not customer:
                # Registrar nuevo cliente
                logger.info(f"Registrando nuevo cliente: {from_number}")
                customer = self.customer_repository.create(from_number, sender_name)
            elif sender_name and not customer.get('name'):
                 # Actualizar nombre si no lo teníamos
                 self.customer_repository.update_name(from_number, sender_name)
                 customer['name'] = sender_name

        # 1. Definir palabras clave
        checkout_keywords = ['confirmar', 'listo', 'finalizar', 'comprar', 'pagar', 'fin', 'total']
        confirmation_keywords = ['si', 'sí', 'ok', 'claro', 'dale', 'bueno']
        greeting_keywords = ['hola', 'buen', 'buenas', 'que tal', 'hey', 'hello', 'hi', 'saludos']
        quote_keywords = ['cotiz', 'precio', 'cuanto', 'quiero', 'necesito', 'tienes', 'dame', 'busca', 'valor', 'costo']

        text_lower = text.lower()

        # 2. Check: Checkout o Confirmación
        # Si dice "Total" o "Confirmar" -> Checkout
        # Si dice "Si" Y tiene sesión -> Checkout
        is_checkout_explicit = any(keyword in text_lower for keyword in checkout_keywords)
        is_confirmation = any(keyword == text_lower or text_lower.startswith(keyword + " ") for keyword in confirmation_keywords)
        
        if is_checkout_explicit or (is_confirmation and len(text.split()) < 4):
            if self.session_repository:
                 # Verificar si realmente tiene sesión antes de asumir checkout
                 session = self.session_repository.get_session(from_number)
                 if session and session.get('items'):
                     return await self._handle_checkout(from_number, message_id, customer)

        # 3. Check: Saludo
        # Si el texto es corto y parece saludo
        if any(keyword in text_lower for keyword in greeting_keywords) and len(text.split()) < 5:
            return await self._handle_greeting(from_number, message_id, customer)

        # 4. Check: Intención de Cotización
        is_quote_intent = any(keyword in text_lower for keyword in quote_keywords)
        
        # Intentar parsear items independientemente de la intención explícita
        # (ej: "2 zapatos" no tiene keyword de cotización pero es una orden)
        try:
            # Intentar generar cotización (parsing)
            # Usamos una función auxiliar o el método existente modificando el manejo de error
            return await self._handle_add_items(from_number, text, message_id, is_quote_intent)

        except ValueError:
            # Si falla el parsing
            if is_quote_intent:
                # Caso: Quiere cotizar pero no se entendió qué
                msg = "🤔 Entiendo que quieres una cotización, pero no logré identificar el producto. ¿Podrías ser más específico? (Ej: '2 zapatos')"
                await self.whatsapp_service.send_message(from_number, msg)
                return {'success': False, 'reason': 'quote_intent_no_products'}
            
            # Caso: Desconocido
            msg = "disculpa, no entendí tu mensaje. ¿Quieres ver precios o hacer un pedido? Intenta escribir algo como 'quiero 2 camisas'."
            await self.whatsapp_service.send_message(from_number, msg)
            return {'success': False, 'reason': 'unknown_intent'}

    async def _handle_greeting(self, from_number: str, message_id: str, customer: Optional[Dict] = None) -> Dict:
        greeting_name = ""
        if customer and customer.get('name'):
            # Usar primer nombre
            first_name = customer['name'].split()[0]
            greeting_name = f" {first_name}"
            
        msg = f"¡Hola{greeting_name}! 👋 Bienvenido a nuestro sistema de cotizaciones.\n\nPuedes pedirme productos escribiendo algo como: *\"Quiero 2 zapatos y 1 camisa\"*."
        await self.whatsapp_service.send_message(from_number, msg)
        await self.whatsapp_service.mark_message_as_read(message_id)
        return {'success': True, 'action': 'greeting'}


    async def _handle_checkout(self, from_number: str, message_id: str, customer: Optional[Dict] = None) -> Dict:
        session = self.session_repository.get_session(from_number)
        if not session or not session.get('items'):
            await self.whatsapp_service.send_message(
                to=from_number,
                message="⚠️ No tienes una cotización activa para confirmar."
            )
            return {'success': False, 'reason': 'no_active_session'}

        # Create final quote from session items
        items = session['items']
        
        # Calculate total
        # Re-verify prices in case they changed? For now, trust session or re-fetch?
        # Better to re-create Quote objects to valid.
        # But QuoteService expects text or exact items. 
        # Let's reconstruct text or manually create Quote object.
        # Manual Quote creation seems safer.
        
        try:
            # Re-validate items through quote service to get fresh prices/objects
            # Or manually construct if we trust session data.
            # Let's manually construct to keep it simple, assuming session has valid data.
            
            quote_text = ", ".join([f"{item['quantity']} {item['product_name']}" for item in items])
            logger.info(f"Generando cotización final para: {quote_text}")
            
            # Use service to generate quote (re-validates prices)
            result = self.quote_service.generate_quote_with_details(
                text=quote_text,
                client_phone=f"+{from_number}",
                notes="Cotización finalizada (Session)"
            )
            quote = result['quote']
            
            # Asociar cliente si existe
            if customer:
                quote.customer_id = customer.get('id')

            # Save to DB
            created_quote = await self.quote_repository.create(quote)
            
            # Send Final Quote
            quote_data = self._entity_to_dict(quote)
            quote_data['id'] = created_quote.id
            quote_data['client_phone'] = quote.client_phone
            
            await self.whatsapp_service.send_quote_message(to=from_number, quote_data=quote_data)
            await self.whatsapp_service.mark_message_as_read(message_id)

            # Clear session
            self.session_repository.delete_session(from_number)
            
            # --- Generar y Subir PDF ---
            try:
                pdf_path = self.invoice_service.generate_invoice_pdf(quote_data)
                
                # Nombre de archivo único: quotes/{phone}/quote_{id}_{timestamp}.pdf
                timestamp = int(datetime.now().timestamp())
                filename = f"quote_{created_quote.id}_{timestamp}.pdf"
                storage_path = f"quotes/{from_number}/{filename}"
                
                public_url = await self.storage_service.upload_pdf(pdf_path, storage_path)
                
                if public_url:
                    # Enviar Documento PDF
                    await self.whatsapp_service.send_document(
                        to=from_number,
                        link=public_url,
                        caption=f"Aquí tienes tu cotización formal 📄 (N° {created_quote.id})"
                    )
                else:
                    # Fallback si no se pudo subir
                    await self.whatsapp_service.send_message(to=from_number, message="Se generó la cotización pero hubo un problema enviando el PDF.")
                
            except Exception as pdf_err:
                logger.error(f"Error generando/subiendo PDF: {pdf_err}")
                # No fallar el checkout si el PDF falla, ya enviamos el resumen por WhatsApp
                await self.whatsapp_service.send_message(to=from_number, message="Cotización guardada exitosamente. Hubo un error técnico generando el PDF.")
                

            
            return {'success': True, 'action': 'checkout', 'quote_id': created_quote.id}

        except Exception as e:
            logger.error(f"Error en checkout: {e}")
            await self.whatsapp_service.send_message(to=from_number, message="❌ Error generando cotización final.")
            return {'success': False, 'error': str(e)}

    async def _handle_add_items(self, from_number: str, text: str, message_id: str, is_quote_intent: bool = False) -> Dict:
        try:
            # 1. Parse new items
            result = self.quote_service.generate_quote_with_details(
                text=text,
                client_phone=f"+{from_number}",
                fuzzy_threshold=70
            )
            new_quote = result['quote']
            
            # Si no hay items, QuoteService debería haber lanzado ValueError,
            # pero por seguridad verificamos
            if not new_quote.items:
                 raise ValueError("No items parsed")

            new_items = self._entity_to_dict(new_quote)['items']

            # 2. Get existing session
            current_items = []
            if self.session_repository:
                session = self.session_repository.get_session(from_number)
                if session:
                    # Check expiry (30 mins)
                    updated_at = datetime.fromisoformat(session['updated_at'].replace('Z', '+00:00'))
                    if datetime.now(updated_at.tzinfo) - updated_at > timedelta(minutes=30):
                        self.session_repository.delete_session(from_number)
                    else:
                        current_items = session.get('items', [])

            # 3. Merge items
            merged_items = self._merge_items(current_items, new_items)

            # 4. Save session
            if self.session_repository:
                self.session_repository.create_or_update_session(from_number, merged_items)

            # 5. Send Partial Summary
            # Calculate partial total locally for speed
            total = sum(item['subtotal'] for item in merged_items)
            
            response_text = "✅ *Productos Agregados*\n\n"
            for item in new_items:
                response_text += f"+ {item['quantity']} {item['product_name']}\n"
            
            response_text += f"\n🛒 *Total Acumulado:* ${total:.2f}\n"
            response_text += "Envia más productos o escribe *'confirmar'* para finalizar."
            
            await self.whatsapp_service.send_message(to=from_number, message=response_text)
            await self.whatsapp_service.mark_message_as_read(message_id)
            
            return {'success': True, 'action': 'add_items', 'items_count': len(merged_items)}

        except ValueError as e:
            # Re-raise to be handled by execute() based on intent
            raise e

    def _merge_items(self, current: List[Dict], new: List[Dict]) -> List[Dict]:
        """Merge new items into current list, summing quantities."""
        merged = {item['product_name']: item for item in current}
        
        for item in new:
            name = item['product_name']
            if name in merged:
                merged[name]['quantity'] += item['quantity']
                merged[name]['subtotal'] += item['subtotal'] # Aprox, should recalc unit * qty
                # Recalculate subtotal correctly
                merged[name]['subtotal'] = merged[name]['quantity'] * merged[name]['unit_price']
            else:
                merged[name] = item
                
        return list(merged.values())

    def _entity_to_dict(self, quote) -> Dict:
        """Helper to convert quote entity to dict for JSON serialization."""
        return {
            'items': [
                {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'subtotal': item.subtotal,
                    'description': getattr(item, 'description', '')
                }
                for item in quote.items
            ],
            'total': quote.total
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
