from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
import logging
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService
from ....domain.services import QuoteService

if TYPE_CHECKING:
    from ....infrastructure.external.groq_service import GroqService

logger = logging.getLogger(__name__)

class QuoteHandler(WhatsAppHandler):
    """
    Maneja la intención de cotizar o agregar items al carrito.
    Incluye lógica de parseo, comandos fuertes de edición y fallback a Gemini.
    """
    
    def __init__(
        self, 
        whatsapp_service: WhatsAppService,
        quote_service: QuoteService,
        session_repository,
        groq_service: Optional['GroqService'] = None
    ):
        self.whatsapp_service = whatsapp_service
        self.quote_service = quote_service
        self.session_repository = session_repository
        
        if groq_service:
            self.groq_service = groq_service
        else:
            from ....infrastructure.external.groq_service import GroqService
            self.groq_service = GroqService()

    async def handle(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        text = message_data.get('text', '').strip()
        message_id = message_data.get('message_id')
        is_quote_intent = message_data.get('is_quote_intent', False)
        
        # Intentar manejo principal (parseo de productos)
        try:
            return await self._handle_add_items(from_number, text, message_id)
        except ValueError:
            # Fallback Logic
            # Si is_quote_intent era True, significa que detectamos keywords pero el parser falló
            if is_quote_intent:
                msg = "🤔 Entiendo que quieres una cotización, pero no logré identificar el producto. ¿Podrías decirme qué necesitas exactamente?"
                await self.whatsapp_service.send_message(from_number, msg)
                return {'success': False, 'reason': 'quote_intent_no_products'}
            
            # Si llegamos aquí y no era quote intent explicito pero el dispatcher lo mandó (ej. fallback general)
            # Intentamos con Groq
            response_text = await self.groq_service.get_fallback_response(text)
            await self.whatsapp_service.send_message(from_number, response_text)
            return {'success': True, 'action': 'fallback_ai'}

    async def _handle_add_items(self, from_number: str, text: str, message_id: str) -> Dict:
        text_lower = text.lower()
        delete_keywords = ['elimina', 'quita', 'borra', 'saca', 'remover', 'quitar']
        
        # ¿Es un comando de edición fuerte?
        is_strong_command = any(kw in text_lower for kw in delete_keywords + ['solo deja', 'reemplaza', 'sustituye', 'cambia por', 'coloca', 'pon', 'agrega'])

        # 1. Parsear con detalles
        # Usamos try/except para capturar el ValueError si no hay items
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
            new_final_items = []
            
            for item_detail in parsed_items:
                matched_val = item_detail['matched_text'].lower()
                start_pos = text_lower.find(matched_val)
                context_before = text_lower[max(0, start_pos-25):start_pos]
                is_negated = any(kw in context_before for kw in delete_keywords)
                
                if not is_negated:
                    product_data = self._entity_to_dict_item(item_detail)
                    new_final_items.append(product_data)
                else:
                    logger.info(f"Ítem negado por contexto: {matched_val}")
            
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
