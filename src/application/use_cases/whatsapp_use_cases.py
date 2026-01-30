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

        # 1. Definir todas las palabras clave e intenciones globales
        greeting_keywords = ['hola', 'buen', 'buenas', 'que tal', 'hey', 'hello', 'hi', 'saludos']
        location_keywords = ['ubicacion', 'donde', 'direccion', 'local', 'tienda', 'ubicados', 'horario', 'hora', 'abierto']
        delivery_keywords = ['delivery', 'envio', 'domicilio', 'traer', 'llevan', 'zonas', 'costo de envio']
        payment_keywords = ['pagar', 'pago', 'cuenta', 'zelle', 'binance', 'banco', 'transferencia', 'pago movil', 'bolivares', 'dolares', 'metodos', 'como pago']
        quote_keywords = ['cotiz', 'precio', 'cuanto', 'quiero', 'necesito', 'tienes', 'dame', 'busca', 'valor', 'costo']
        
        checkout_keywords = ['confirmar', 'listo', 'finalizar', 'comprar', 'fin', 'total']
        confirmation_keywords = ['si', 'sí', 'ok', 'claro', 'dale', 'bueno']

        text_lower = text.lower()
        is_quote_intent = any(keyword in text_lower for keyword in quote_keywords)
        is_checkout_explicit = any(keyword in text_lower for keyword in checkout_keywords)

        # 2. INTENCIONES PRIORITARIAS (Interrumpen cualquier flujo)

        # F. VACIAR CARRITO
        empty_cart_keywords = ['vacia', 'vaciar', 'limpiar carrito', 'borrar todo', 'eliminar todo', 'vacía', 'vacíar', 'cancelar pedido']
        if any(keyword in text_lower for keyword in empty_cart_keywords):
             if self.session_repository:
                 self.session_repository.delete_session(from_number)
             
             await self.whatsapp_service.send_message(from_number, "🗑️ Tu carrito ha sido vaciado. ¿Qué te gustaría pedir ahora?")
             return {'success': True, 'action': 'empty_cart'}
        
        # A. Saludo
        if any(keyword in text_lower for keyword in greeting_keywords) and len(text.split()) < 5:
            return await self._handle_greeting(from_number, message_id, customer)

        # B. FAQ: Ubicación / Horario
        if any(keyword in text_lower for keyword in location_keywords):
             from ...infrastructure.services.business_info_service import BusinessInfoService
             business_service = BusinessInfoService()
             direccion = business_service.get_value("direccion", "Centro Comercial El Socorro, Local 12, Valencia.")
             horario = business_service.get_value("horario", "Lunes a Sábado de 8:00 AM a 5:00 PM")
             msg = f"📍 *Nuestra Ubicación:*\n{direccion}\n\n⏰ *Horario de Atención:*\n{horario}"
             await self.whatsapp_service.send_message(from_number, msg)
             return {'success': True, 'action': 'location_info'}

        # C. FAQ: Delivery
        if any(keyword in text_lower for keyword in delivery_keywords):
             from ...infrastructure.services.business_info_service import BusinessInfoService
             business_service = BusinessInfoService()
             has_delivery = business_service.get_value("has_delivery", "true").lower() == "true"
             if not has_delivery:
                 msg = "🚫 *Servicio de Delivery No Disponible*\n\nPor el momento no contamos con servicio de entrega a domicilio. Solo realizamos entregas personales en nuestra tienda física."
             else:
                 info = business_service.get_value("delivery_info", "Realizamos entregas en toda la ciudad.")
                 precio = business_service.get_value("delivery_precio", "Consultar tarifa según zona.")
                 msg = f"🚚 *Servicio de Delivery:*\n{info}\n\n💰 *Tarifas:*\n{precio}"
             await self.whatsapp_service.send_message(from_number, msg)
             return {'success': True, 'action': 'delivery_info'}
             
        # D. FAQ: Métodos de Pago
        if any(keyword in text_lower for keyword in payment_keywords):
             from ...infrastructure.services.business_info_service import BusinessInfoService
             business_service = BusinessInfoService()
             metodos = business_service.get_value("metodos_pago", "Aceptamos Efectivo, Pago Móvil, Zelle y Binance.")
             pm = business_service.get_value("pago_movil", "Solicita los datos de pago móvil.")
             zelle = business_service.get_value("zelle", "")
             binance = business_service.get_value("binance", "")
             msg = f"💳 *Métodos de Pago:* \n{metodos}\n\n"
             if pm: msg += f"📲 *Pago Móvil:* \n{pm}\n\n"
             if zelle: msg += f"🇺🇸 *Zelle:* \n{zelle}\n\n"
             if binance: msg += f"🪙 *Binance:* \n{binance}"
             await self.whatsapp_service.send_message(from_number, msg.strip())
             return {'success': True, 'action': 'payment_info'}

        # E. Nueva Cotización o Agregar Items (Incluso si estamos en wizard, esto permite 'escapar' para comprar más)
        if is_quote_intent:
            try:
                return await self._handle_add_items(from_number, text, message_id, is_quote_intent)
            except ValueError:
                # Si falló el parseo pero era intención clara, avisamos
                msg = "🤔 Entiendo que quieres una cotización, pero no logré identificar el producto. ¿Podrías decirme qué necesitas exactamente?"
                await self.whatsapp_service.send_message(from_number, msg)
                return {'success': False, 'reason': 'quote_intent_no_products'}

        # 3. GESTIÓN DE WIZARD (Recolección de Datos)
        if self.session_repository:
            session = self.session_repository.get_session(from_number)
            if session:
                step = session.get('conversation_step', 'shopping')
                client_data = session.get('client_data', {}) or {}
                
                # --- Validaciones de Estado ---
                
                # A. Esperando Nombre
                if step == 'WAITING_NAME':
                    # Validación básica: No debe ser un número largo ni tener palabras clave de otras cosas
                    if len(text.split()) > 6 or any(kw in text_lower for kw in ['precio', 'cuanto', 'delivery', 'pago']):
                        await self.whatsapp_service.send_message(from_number, "🤔 Disculpa, ¿podrías indicarme tu **Nombre y Apellido** para continuar con el registro?")
                        return {'success': False, 'reason': 'invalid_name_input'}
                        
                    client_data['name'] = text
                    self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_DNI', client_data=client_data)
                    await self.whatsapp_service.send_message(from_number, "✅ Guardado. Ahora indícame tu **Cédula o RIF**:")
                    return {'success': True, 'action': 'saved_name'}
                
                # B. Esperando DNI
                if step == 'WAITING_DNI':
                    # Validación omitida para RIFs alfanuméricos, pero checkeamos longitud mínima razonable
                    if len(text) < 5 or len(text) > 15:
                         await self.whatsapp_service.send_message(from_number, "⚠️ Por favor, envíame un **Cédula o RIF** válido para procesar tu nota de entrega.")
                         return {'success': False, 'reason': 'invalid_dni_input'}

                    client_data['dni'] = text
                    self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_ADDRESS', client_data=client_data)
                    await self.whatsapp_service.send_message(from_number, "👍 Listo. Por último, envíame tu **Dirección Fiscal / Entrega**:")
                    return {'success': True, 'action': 'saved_dni'}
                
                # C. Esperando Dirección -> Confirmación Final
                if step == 'WAITING_ADDRESS':
                    if len(text) < 5:
                         await self.whatsapp_service.send_message(from_number, "📍 Por favor, indícame la **Dirección** lo más detallada posible.")
                         return {'success': False, 'reason': 'invalid_address_input'}

                    client_data['address'] = text
                    self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_FINAL_CONFIRMATION', client_data=client_data)
                    
                    items = session.get('items', [])
                    total = sum(item['subtotal'] for item in items)
                    summary = "📝 **Confirma tus Datos**\n\n"
                    summary += f"👤 *Nombre:* {client_data.get('name')}\n"
                    summary += f"🆔 *CI/RIF:* {client_data.get('dni')}\n"
                    summary += f"📍 *Dirección:* {text}\n\n"
                    summary += "📦 *Tu Pedido:*\n"
                    for item in items: summary += f"- {item['quantity']} {item['product_name']}\n"
                    summary += f"\n💰 *Total a registrar:* ${total:.2f}\n\n"
                    summary += "👉 Si todo es correcto, escribe **'SÍ'**.\n"
                    summary += "👉 Si hay algo que corregir, escribe **'NO'**."
                    await self.whatsapp_service.send_message(from_number, summary)
                    return {'success': True, 'action': 'request_final_confirmation'}

                # D. Confirmación Final
                if step == 'WAITING_FINAL_CONFIRMATION':
                    confirm_yes = ['si', 'sí', 'ok', 'correcto', 'dale', 'confirmar']
                    confirm_no = ['no', 'corregir', 'mal', 'incorrecto', 'error']
                    if any(kw == text_lower or text_lower.startswith(kw + " ") for kw in confirm_yes):
                        self.session_repository.create_or_update_session(from_number, conversation_step='PROCESSING_CHECKOUT', client_data=client_data)
                        return await self._handle_checkout(from_number, message_id, customer, client_data)
                    elif any(kw in text_lower for kw in confirm_no):
                        self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_NAME')
                        await self.whatsapp_service.send_message(from_number, "Entendido. Empecemos de nuevo. Por favor, indícame tu **Nombre y Apellido** correctos.")
                        return {'success': True, 'action': 'reset_wizard'}
                    else:
                        await self.whatsapp_service.send_message(from_number, "⚠️ Por favor responde **SÍ** para finalizar o **NO** para corregir los datos.")
                        return {'success': False, 'action': 'ambiguous_response'}

        # 4. INICIO DE WIZARD (Solo si no hubo intención global arriba)
        is_confirmation = any(keyword == text_lower or text_lower.startswith(keyword + " ") for keyword in confirmation_keywords)
        
        if is_checkout_explicit or (is_confirmation and len(text.split()) < 4):
            if self.session_repository:
                 session = self.session_repository.get_session(from_number)
                 if session and session.get('items'):
                     self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_NAME')
                     await self.whatsapp_service.send_message(from_number, "¡Excelente elección! 📝 Para generar tu recibo, por favor indícame tu **Nombre y Apellido**.")
                     return {'success': True, 'action': 'wizard_started'}

        # 5. FALLBACK: Gemini AI (Solo si llegamos aquí sin match)
        try:
            # Re-intento de parseo por si acaso fue algo muy sutil que no captó 'is_quote_intent'
            return await self._handle_add_items(from_number, text, message_id, False)
        except ValueError:
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
                f"¡Hola de nuevo, {first_name}! 👋\n\n"
                "Adjunto encontrarás nuestro catálogo actualizado 📂.\n\n"
                "Estoy listo para tomar tu pedido. Dime qué necesitas.\n\n"
                "Ejemplos:\n"
                "🔹 'Precio de los zapatos'\n"
                "🔹 'Quiero 2 chemises'"
            )
        else:
            msg = (
                "¡Hola! 👋 Bienvenido.\n\n"
                "Aquí tienes nuestro catálogo actualizado 📂.\n\n"
                "Puedes pedirme lo que necesites como si hablaras con un vendedor.\n\n"
                "Ejemplos:\n"
                "🔹 'Precio de los zapatos'\n"
                "🔹 'Quiero 2 chemises'"
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
                        caption="Aquí tienes nuestro catálogo 2026 📂",
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
        text_lower = text.lower()
        delete_keywords = ['elimina', 'quita', 'borra', 'saca', 'remover', 'quitar']
        replace_keywords = ['solo deja', 'reemplaza', 'sustituye', 'cambia por', 'coloca', 'pon', 'agrega']
        
        # ¿Es un comando de edición fuerte?
        is_strong_command = any(kw in text_lower for kw in delete_keywords + ['solo deja', 'reemplaza'])

        try:
            # 1. Parsear con detalles (necesitamos matched_text para contexto)
            result = self.quote_service.generate_quote_with_details(
                text=text,
                client_phone=f"+{from_number}",
                fuzzy_threshold=70
            )
            parsed_items = result.get('parsed_items', [])
            
            if not parsed_items:
                 raise ValueError("No items parsed")

            # 2. Obtener sesión actual
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

            # 3. Lógica de "Limpieza y Re-procesamiento" si es comando fuerte
            if is_strong_command:
                logger.info(f"Comando fuerte detectado en: {text}. Reiniciando ítems para re-edición.")
                # Reiniciamos la base para solo procesar lo que viene en este mensaje según su contexto
                new_final_items = []
                
                # Para cada producto detectado, vemos si tiene un "quita" cerca
                for item_detail in parsed_items:
                    matched_val = item_detail['matched_text'].lower()
                    # Buscar la posición del match para ver el contexto previo
                    start_pos = text_lower.find(matched_val)
                    # Miramos unos 20 caracteres antes del match
                    context_before = text_lower[max(0, start_pos-25):start_pos]
                    
                    is_negated = any(kw in context_before for kw in delete_keywords)
                    
                    if not is_negated:
                        # Si no está negado, lo agregamos como nuevo ítem
                        product_data = self._entity_to_dict_item(item_detail)
                        new_final_items.append(product_data)
                    else:
                        logger.info(f"Ítem negado por contexto: {matched_val}")
                
                # En comando fuerte, el carrito resultante es EXCLUSIVAMENTE lo no negado de este mensaje
                merged_items = new_final_items
                action_description = "Carrito Actualizado"
            else:
                # Lógica Normal: Mezclar ítems detectados con el carrito actual
                new_items_to_add = [self._entity_to_dict_item(item) for item in parsed_items]
                merged_items = self._merge_items(current_items, new_items_to_add)
                action_description = "Productos Agregados"

            # 4. Guardar sesión
            if self.session_repository:
                if not merged_items:
                     self.session_repository.delete_session(from_number)
                else:
                     self.session_repository.create_or_update_session(from_number, merged_items)

            # 5. Respuesta al usuario
            total = sum(item['subtotal'] for item in merged_items)
            response_text = f"✅ *{action_description}*\n\n"
            
            # Mostrar que quedó en el carrito
            if not merged_items:
                response_text = "🗑️ Tu carrito ha sido vaciado."
            else:
                for item in merged_items:
                    response_text += f"• {item['quantity']} {item['product_name']}\n"
                
                response_text += f"\n💰 *Total Actual:* ${total:.2f}\n"
                response_text += "Escribe *'confirmar'* para finalizar o sigue agregando."
            
            await self.whatsapp_service.send_message(to=from_number, message=response_text)
            await self.whatsapp_service.mark_message_as_read(message_id)
            
            return {'success': True, 'action': 'edit_cart', 'items_count': len(merged_items)}

        except ValueError:
            raise

    def _entity_to_dict_item(self, parsed_item: Dict) -> Dict:
        """Convierte item del parser a formato de sesión."""
        product = parsed_item['product']
        qty = parsed_item['quantity']
        price = product['price']
        return {
            'product_name': product['name'],
            'quantity': qty,
            'unit_price': price,
            'subtotal': price * qty,
            'description': product.get('category', '')
        }

    def _merge_items(self, current: List[Dict], new: List[Dict]) -> List[Dict]:
        """Mezcla ítems sumando cantidades."""
        merged = {item['product_name']: item for item in current}
        for item in new:
            name = item['product_name']
            if name in merged:
                merged[name]['quantity'] += item['quantity']
                merged[name]['subtotal'] = merged[name]['quantity'] * merged[name]['unit_price']
            else:
                merged[name] = item
        return list(merged.values())

    def _entity_to_dict(self, quote) -> Dict:
        """Convertir entidad Quote a dict."""
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
