from typing import Dict
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService

class WizardHandler(WhatsAppHandler):
    """
    Maneja el flujo de conversación (Wizard) para recolección de datos.
    """
    
    def __init__(self, whatsapp_service: WhatsAppService, session_repository):
        self.whatsapp_service = whatsapp_service
        self.session_repository = session_repository

    async def handle(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        text = message_data.get('text', '').strip()
        text_lower = text.lower()
        
        session = self.session_repository.get_session(from_number)
        if not session:
             return {'success': False, 'reason': 'no_session'}

        step = session.get('conversation_step', 'shopping')
        client_data = session.get('client_data', {}) or {}
        
        # A. Esperando Nombre
        if step == 'WAITING_NAME':
            # Validación básica
            if len(text.split()) > 6 or any(kw in text_lower for kw in ['precio', 'cuanto', 'delivery', 'pago']):
                await self.whatsapp_service.send_message(from_number, "🤔 Disculpa, ¿podrías indicarme tu **Nombre y Apellido** para continuar con el registro?")
                return {'success': False, 'reason': 'invalid_name_input'}
                
            client_data['name'] = text
            self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_DNI', client_data=client_data)
            await self.whatsapp_service.send_message(from_number, "✅ Guardado. Ahora indícame tu **Cédula o RIF**:")
            return {'success': True, 'action': 'saved_name'}
        
        # B. Esperando DNI
        if step == 'WAITING_DNI':
            if len(text) < 5 or len(text) > 15:
                    await self.whatsapp_service.send_message(from_number, "⚠️ Por favor, envíame un **Cédula o RIF** válido para procesar tu nota de entrega.")
                    return {'success': False, 'reason': 'invalid_dni_input'}

            client_data['dni'] = text
            self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_ADDRESS', client_data=client_data)
            await self.whatsapp_service.send_message(from_number, "👍 Listo. Por último, envíame tu **Dirección Fiscal / Entrega**:")
            return {'success': True, 'action': 'saved_dni'}
        
        # C. Esperando Dirección
        if step == 'WAITING_ADDRESS':
            if len(text) < 5:
                # Si es muy corto, pedimos más detalles (aquí seguimos usando texto)
                await self.whatsapp_service.send_message(from_number, "⚠️ La dirección es muy corta. Por favor sé un poco más específico.")
                return {'success': False, 'reason': 'short_address'}

            client_data['address'] = text
            self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_FINAL_CONFIRMATION', client_data=client_data)
            
            # Generar Resumen
            items = session.get('items', [])
            total = sum(item['subtotal'] for item in items)
            
            summary = "📝 *Confirma tus Datos*\n\n"
            summary += f"👤 *Nombre:* {client_data.get('name')}\n"
            summary += f"🆔 *CI/RIF:* {client_data.get('dni')}\n"
            summary += f"📍 *Dirección:* {text}\n\n"
            summary += f"💰 *Total a pagar:* ${total:.2f}\n\n"
            summary += "¿Los datos son correctos?"

            # Enviar Botones Interactivos
            buttons = [
                {'id': 'confirm_checkout', 'title': '✅ Confirmar'},
                {'id': 'edit_data', 'title': '✏️ Corregir'}
            ]
            
            await self.whatsapp_service.send_interactive_button(from_number, summary, buttons)
            return {'success': True, 'action': 'request_final_confirmation'}

        # D. Confirmación Final
        if step == 'WAITING_FINAL_CONFIRMATION':
            button_payload = message_data.get('button_payload')
            
            # Detectar confirmación (Botón o Texto)
            is_confirmed = (button_payload == 'confirm_checkout') or \
                           any(kw in text_lower for kw in ['si', 'sí', 'ok', 'correcto', 'dale', 'confirmar'])
            
            # Detectar corrección
            is_edit = (button_payload == 'edit_data') or \
                      any(kw in text_lower for kw in ['no', 'corregir', 'mal', 'incorrecto', 'error'])

            if is_confirmed:
                # Delegamos al CheckoutHandler a través del Dispatcher
                # No cambiamos step aquí, dejamos que checkout lo limpie o lo maneje
                return {'success': True, 'action': 'trigger_checkout'}
            
            elif is_edit:
                self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_NAME')
                await self.whatsapp_service.send_message(from_number, "Entendido. Empecemos de nuevo. Por favor, indícame tu **Nombre y Apellido** correctos.")
                return {'success': True, 'action': 'reset_wizard'}
            
            else:
                await self.whatsapp_service.send_message(from_number, "⚠️ Por favor selecciona una opción o escribe **SÍ** para finalizar.")
                return {'success': False, 'action': 'ambiguous_response'}
        
        # E. Confirmación de Datos Ya Registrados (Nuevo Flow)
        if step == 'WAITING_EXISTING_DATA_CONFIRMATION':
            button_payload = message_data.get('button_payload')
            
            is_confirmed = (button_payload == 'confirm_existing') or \
                           any(kw in text_lower for kw in ['si', 'sí', 'usar estos', 'correctos', 'bien', 'usar'])
            
            is_update = (button_payload == 'update_data') or \
                        any(kw in text_lower for kw in ['no', 'actualizar', 'cambiar', 'corregir', 'nuevos'])

            if is_confirmed:
                return {'success': True, 'action': 'trigger_checkout'}
            
            elif is_update:
                self.session_repository.create_or_update_session(from_number, conversation_step='WAITING_NAME', client_data={})
                await self.whatsapp_service.send_message(from_number, "📝 Entendido. Actualicemos tus datos.\n\nPor favor, indícame tu **Nombre y Apellido**:")
                return {'success': True, 'action': 'start_update_wizard'}
            
            else:
                await self.whatsapp_service.send_message(from_number, "⚠️ Por favor confirma si los datos son correctos o si deseas actualizarlos.")
                return {'success': False, 'action': 'ambiguous_response'}

        return {'success': False, 'reason': 'unknown_step'}
