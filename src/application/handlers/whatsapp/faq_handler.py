from typing import Dict
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService
from ....infrastructure.services.business_info_service import BusinessInfoService

class FAQHandler(WhatsAppHandler):
    """
    Maneja preguntas frecuentes: Ubicación, Delivery, Métodos de Pago.
    """
    
    def __init__(self, whatsapp_service: WhatsAppService):
        self.whatsapp_service = whatsapp_service
        self.business_service = BusinessInfoService()

    async def handle(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        intent = message_data.get('intent') # location, delivery, payment
        
        if intent == 'location':
            direccion = self.business_service.get_value("direccion", "Centro Comercial El Socorro, Local 12, Valencia.")
            horario = self.business_service.get_value("horario", "Lunes a Sábado de 8:00 AM a 5:00 PM")
            msg = f"📍 *Nuestra Ubicación:*\n{direccion}\n\n⏰ *Horario de Atención:*\n{horario}"
            await self.whatsapp_service.send_message(from_number, msg)
            return {'success': True, 'action': 'location_info'}
            
        elif intent == 'delivery':
            has_delivery = self.business_service.get_value("has_delivery", "true").lower() == "true"
            if not has_delivery:
                msg = "🚫 *Servicio de Delivery No Disponible*\n\nPor el momento no contamos con servicio de entrega a domicilio. Solo realizamos entregas personales en nuestra tienda física."
            else:
                info = self.business_service.get_value("delivery_info", "Realizamos entregas en toda la ciudad.")
                precio = self.business_service.get_value("delivery_precio", "Consultar tarifa según zona.")
                msg = f"🚚 *Servicio de Delivery:*\n{info}\n\n💰 *Tarifas:*\n{precio}"
            await self.whatsapp_service.send_message(from_number, msg)
            return {'success': True, 'action': 'delivery_info'}
            
        elif intent == 'payment':
            metodos = self.business_service.get_value("metodos_pago", "Aceptamos Efectivo, Pago Móvil, Zelle y Binance.")
            pm = self.business_service.get_value("pago_movil", "Solicita los datos de pago móvil.")
            zelle = self.business_service.get_value("zelle", "")
            binance = self.business_service.get_value("binance", "")
            msg = f"💳 *Métodos de Pago:* \n{metodos}\n\n"
            if pm: msg += f"📲 *Pago Móvil:* \n{pm}\n\n"
            if zelle: msg += f"🇺🇸 *Zelle:* \n{zelle}\n\n"
            if binance: msg += f"🪙 *Binance:* \n{binance}"
            await self.whatsapp_service.send_message(from_number, msg.strip())
            return {'success': True, 'action': 'payment_info'}
            
        return {'success': False, 'reason': 'unknown_faq_intent'}
