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

        # --- Gestión de Clientes (CRM) ---
        # Buscamos cliente por teléfono para tener contexto
        customer = None
        if self.customer_repository:
            # Usamos el servicio si posible, sino repo directo (wrapper local)
            # Para simplificar sin inyectar CustomerService en constructor todavía (refactor menor)
            from ...infrastructure.services.customer_service import CustomerService
            c_service = CustomerService(self.customer_repository)
            customer = c_service.get_customer_by_phone(from_number)
            
            if customer:
                logger.info(f"Cliente identificado: {customer.get('full_name')} ({customer.get('id')})")
            else:
                logger.info(f"Cliente nuevo detectado: {from_number}")

        # 1. Definir palabras clave
        checkout_keywords = ['confirmar', 'listo', 'finalizar', 'comprar', 'pagar', 'fin', 'total']
        confirmation_keywords = ['si', 'sí', 'ok', 'claro', 'dale', 'bueno']

        greeting_keywords = ['hola', 'buen', 'buenas', 'que tal', 'hey', 'hello', 'hi', 'saludos']
        quote_keywords = ['cotiz', 'precio', 'cuanto', 'quiero', 'necesito', 'tienes', 'dame', 'busca', 'valor', 'costo']

        text_lower = text.lower()

        # 2. Check: Session State Machine (Wizard de Datos)
        if self.session_repository:
            session = self.session_repository.get_session(from_number)
            if session:
                step = session.get('conversation_step', 'shopping')
                client_data = session.get('client_data', {}) or {}
                
                # Estado: Esperando Nombre
                if step == 'WAITING_NAME':
                    client_data['name'] = text
                    self.session_repository.create_or_update_session(
                        from_number, 
                        conversation_step='WAITING_DNI',
                        client_data=client_data
                    )
                    await self.whatsapp_service.send_message(
                        from_number, 
                        "✅ Guardado. Ahora indícame tu **Cédula o RIF**:"
                    )
                    return {'success': True, 'action': 'saved_name'}
                
                # Estado: Esperando DNI
                if step == 'WAITING_DNI':
                    client_data['dni'] = text
                    self.session_repository.create_or_update_session(
                        from_number, 
                        conversation_step='WAITING_ADDRESS',
                        client_data=client_data
                    )
                    await self.whatsapp_service.send_message(
                        from_number, 
                        "👍 Listo. Por último, envíame tu **Dirección Fiscal / Entrega**:"
                    )
                    return {'success': True, 'action': 'saved_dni'}
                
                # Estado: Esperando Dirección -> Confirmación Final
                if step == 'WAITING_ADDRESS':
                    client_data['address'] = text
                    self.session_repository.create_or_update_session(
                        from_number, 
                        conversation_step='WAITING_FINAL_CONFIRMATION',
                        client_data=client_data
                    )
                    
                    # Generar resumen para confirmar
                    items = session.get('items', [])
                    total = sum(item['subtotal'] for item in items)
                    
                    summary = "📝 **Confirma tus Datos**\n\n"
                    summary += f"👤 *Nombre:* {client_data.get('name')}\n"
                    summary += f"🆔 *CI/RIF:* {client_data.get('dni')}\n"
                    summary += f"📍 *Dirección:* {text}\n\n"
                    
                    summary += "📦 *Tu Pedido:*\n"
                    for item in items:
                         summary += f"- {item['quantity']} {item['product_name']}\n"
                    summary += f"\n💰 *Total a registrar:* ${total:.2f}\n\n"
                    
                    summary += "👉 Si todo es correcto, escribe **'SÍ'**.\n"
                    summary += "👉 Si hay algo que corregir, escribe **'NO'**."
                    
                    await self.whatsapp_service.send_message(from_number, summary)
                    return {'success': True, 'action': 'request_final_confirmation'}

                # Estado: Confirmación Final
                if step == 'WAITING_FINAL_CONFIRMATION':
                    # Palabras de confirmación re-definidas por claridad en este scope
                    confirm_yes = ['si', 'sí', 'ok', 'correcto', 'dale', 'confirmar']
                    confirm_no = ['no', 'corregir', 'mal', 'incorrecto', 'error']
                    
                    if any(kw == text_lower or text_lower.startswith(kw + " ") for kw in confirm_yes):
                        # Confirmado -> Ir a checkout definitivo
                        # Actualizamos estado para prevenir re-entrada si falla algo
                        self.session_repository.create_or_update_session(
                            from_number,
                            conversation_step='PROCESSING_CHECKOUT',
                            client_data=client_data
                        )
                        return await self._handle_checkout(from_number, message_id, customer, client_data)
                        
                    elif any(kw in text_lower for kw in confirm_no):
                        # Negado -> Reiniciar Wizard
                        self.session_repository.create_or_update_session(
                            from_number,
                            conversation_step='WAITING_NAME',
                            # Mantenemos client_data anterior? No, el usuario pidió corregir. O talvez sí para UX, pero el requerimiento dice "Empecemos de nuevo"
                        )
                        await self.whatsapp_service.send_message(
                            from_number,
                            "Entendido. Empecemos de nuevo. Por favor, indícame tu **Nombre y Apellido** correctos."
                        )
                        return {'success': True, 'action': 'reset_wizard'}
                    
                    else:
                        await self.whatsapp_service.send_message(
                            from_number,
                            "⚠️ Por favor responde **SÍ** para finalizar o **NO** para corregir los datos."
                        )
                        return {'success': False, 'action': 'ambiguous_response'}

        # 3. Check: Checkout o Confirmación (Inicio del Wizard)
        # Si dice "Total" o "Confirmar" -> Iniciar Recolección de Datos
        is_checkout_explicit = any(keyword in text_lower for keyword in checkout_keywords)
        is_confirmation = any(keyword == text_lower or text_lower.startswith(keyword + " ") for keyword in confirmation_keywords)
        
        if is_checkout_explicit or (is_confirmation and len(text.split()) < 4):
            if self.session_repository:
                 session = self.session_repository.get_session(from_number)
                 if session and session.get('items'):
                     # INICIO WIZARD: Pedir Nombre
                     self.session_repository.create_or_update_session(
                         from_number, 
                         conversation_step='WAITING_NAME'
                     )
                     await self.whatsapp_service.send_message(
                        from_number, 
                        "¡Excelente elección! 📝 Para generar tu recibo, por favor indícame tu **Nombre y Apellido**."
                     )
                     return {'success': True, 'action': 'wizard_started'}

        # 4. Check: Saludo
        if any(keyword in text_lower for keyword in greeting_keywords) and len(text.split()) < 5:
            return await self._handle_greeting(from_number, message_id, customer)

        # 5. Check: Ubicación / Dirección / Horario (FAQ)
        location_keywords = ['ubicacion', 'donde', 'direccion', 'local', 'tienda', 'ubicados', 'horario', 'hora', 'abierto']
        if any(keyword in text_lower for keyword in location_keywords):
             from ...infrastructure.services.business_info_service import BusinessInfoService
             business_service = BusinessInfoService()
             
             # Obtener info dinámica de BD (con defaults por seguridad)
             direccion = business_service.get_value("direccion", "Centro Comercial El Socorro, Local 12, Valencia.")
             horario = business_service.get_value("horario", "Lunes a Sábado de 8:00 AM a 5:00 PM")
             
             msg = f"📍 *Nuestra Ubicación:*\n{direccion}\n\n⏰ *Horario de Atención:*\n{horario}"
             await self.whatsapp_service.send_message(from_number, msg)
             return {'success': True, 'action': 'location_info'}

        # 6. Check: Intención de Cotización
        is_quote_intent = any(keyword in text_lower for keyword in quote_keywords)
        
        try:
            return await self._handle_add_items(from_number, text, message_id, is_quote_intent)

        except ValueError:
            if is_quote_intent:
                msg = "🤔 Entiendo que quieres una cotización, pero no logré identificar el producto. ¿Podrías ser más específico? (Ej: '2 zapatos')"
                await self.whatsapp_service.send_message(from_number, msg)
                return {'success': False, 'reason': 'quote_intent_no_products'}
            
            # Fallback a Gemini AI
            from ...infrastructure.external.gemini_service import GeminiService
            gemini = GeminiService()
            response_text = await gemini.get_fallback_response(text)
            
            await self.whatsapp_service.send_message(from_number, response_text)
            return {'success': True, 'action': 'fallback_ai'}

    async def _handle_greeting(self, from_number: str, message_id: str, customer: Optional[Dict] = None) -> Dict:
        # 1. Enviar Mensaje de Bienvenida Textual
        if customer and customer.get('full_name'):
            first_name = customer['full_name'].split()[0]
            msg = (
                f"¡Hola, {first_name}! 👋 Bienvenido de vuelta.\n"
                "📂 Te adjunto nuestro catálogo actualizado.\n"
                "Ya conoces el proceso: escríbeme qué necesitas y te ayudo al instante. Ej:\n"
                "👉 'Precio de las gomas'\n"
                "👉 'Quiero 2 chemises'\n"
                "¡Estoy listo!"
            )
        else:
            msg = (
                "¡Hola! 👋 Bienvenido a nuestro sistema de cotizaciones.\n"
                "📂 Te adjunto nuestro catálogo actualizado.\n"
                "Para cotizar, escríbeme como si hablaras con un vendedor. Por ejemplo:\n"
                "👉 'Precio de las gomas'\n"
                "👉 'Quiero 2 chemises y 1 pantalón'\n"
                "¡Estoy listo para atenderte!"
            )
            
        await self.whatsapp_service.send_message(from_number, msg)

        # 2. Enviar Catálogo PDF
        try:
            # Obtener productos y generar catálogo
            products = self.quote_service.get_available_products()
            if products:
                catalog_path = self.invoice_service.generate_catalog_pdf(products)
                storage_path = f"catalogs/catalogo_actual.pdf"
                
                # Subir o actualizar catálogo
                public_url = await self.storage_service.upload_pdf(catalog_path, storage_path)
                
                if public_url:
                    await self.whatsapp_service.send_document(
                        to=from_number,
                        link=public_url,
                        caption="📂 A continuación, el catálogo actualizado:",
                        filename="Catalogo_Productos_2026.pdf"
                    )
        except Exception as e:
            logger.error(f"Error enviando catálogo: {e}")
        await self.whatsapp_service.mark_message_as_read(message_id)
        return {'success': True, 'action': 'greeting'}


    async def _handle_checkout(self, from_number: str, message_id: str, customer: Optional[Dict] = None, client_data: Dict = {}) -> Dict:
        session = self.session_repository.get_session(from_number)
        if not session or not session.get('items'):
            await self.whatsapp_service.send_message(
                to=from_number,
                message="⚠️ No tienes una cotización activa para confirmar."
            )
            return {'success': False, 'reason': 'no_active_session'}

        # Create final quote from session items
        items = session['items']
        
        try:
            quote_text = ", ".join([f"{item['quantity']} {item['product_name']}" for item in items])
            logger.info(f"Generando cotización final para: {quote_text}")
            
            # Use service to generate quote (re-validates prices)
            result = self.quote_service.generate_quote_with_details(
                text=quote_text,
                client_phone=f"+{from_number}",
                notes="Cotización finalizada (Session)"
            )
            quote = result['quote']
            
            # --- ASIGNAR DATOS DEL WIZARD ---
            quote.client_name = client_data.get('name')
            quote.client_dni = client_data.get('dni')
            quote.client_address = client_data.get('address')

            # --- Vincular Cliente CRM ---
            if self.customer_repository:
                try:
                    from ...infrastructure.services.customer_service import CustomerService
                    c_service = CustomerService(self.customer_repository)
                    
                    # Registrar o Actualizar con el nombre confirmado
                    final_customer = c_service.get_or_create_customer(from_number, quote.client_name)
                    
                    if final_customer:
                        # Actualizar dirección
                        if quote.client_address:
                            c_service.update_customer_address(final_customer['id'], quote.client_address)
                        
                        quote.customer_id = final_customer['id']
                        logger.info(f"Cotización vinculada a cliente {final_customer['id']}")
                except Exception as crm_err:
                     logger.error(f"Error CRM: {crm_err}")
            
            # Inicializar notes si es None para evitar TypeError
            if quote.notes is None:
                quote.notes = ""
                
            if quote.client_name:
                 quote.notes += f" | Cliente: {quote.client_name} - {quote.client_dni}"

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
                    # Sanitizar nombre para archivo (alfanumérico y guiones bajos)
                    safe_name = "".join(c if c.isalnum() else "_" for c in (created_quote.client_name or "Cliente"))
                    # Evitar múltiples guiones bajos seguidos
                    while "__" in safe_name:
                        safe_name = safe_name.replace("__", "_")
                    
                    pdf_filename = f"Cotizacion_N_{created_quote.id}_{safe_name}.pdf"

                    # Enviar Documento PDF
                    await self.whatsapp_service.send_document(
                        to=from_number,
                        link=public_url,
                        caption=f"Aquí tienes tu cotización formal 📄 (N° {created_quote.id})",
                        filename=pdf_filename
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

            # Guardar cotización en base de datos (Persistencia de auditoría y dashboard)
            # REMOVED: Se elimina la creación parcial para evitar desorden. Solo se guarda al final.
            # try:
            #     logger.info(f"Guardando cotización parcial en base de datos para {from_number}...")
            #     await self.quote_repository.create(new_quote)
            # except Exception as db_err:
            #     logger.error(f"Error persistiendo cotización: {db_err}")


            
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

        except ValueError:
            raise

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
            'total': quote.total,
            'client_name': quote.client_name,
            'client_dni': quote.client_dni,
            'client_address': quote.client_address
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
