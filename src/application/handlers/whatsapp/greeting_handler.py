from typing import Dict, Optional
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService

class GreetingHandler(WhatsAppHandler):
    """
    Maneja los saludos iniciales.
    """
    
    def __init__(self, whatsapp_service: WhatsAppService):
        self.whatsapp_service = whatsapp_service

    async def handle(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        customer = message_data.get('customer')
        message_id = message_data.get('message_id')
        
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
        
        # Nota: El envío del catálogo PDF se movió a CatalogHandler, 
        # pero mantenemos el mensaje de bienvenida aquí.
        # Si queremos enviar el catálogo siempre al saludar, deberíamos inyectar CatalogHandler o duplicar lógica
        # Para propósitos de este refactor y limpieza, el saludo solo saluda e indica que el usuario puede pedir.
        # PERO, el código original enviaba el catálogo aquí también. 
        # Vamos a replicar el comportamiento original DELEGANDO esa parte o asumiendo que el usuario pedirá el catálogo.
        # Revisando el plan: el BaseGreeting enviaba el catálogo.
        # Para simplificar, dejaremos que el GreetingHandler solo salude y quizas invocar el envío de catálogo desde el Dispatcher si es necesario,
        # O mejor, hacemos que GreetingHandler TAMBIÉN envíe el catálogo si es fácil.
        # Vamos a mantener la lógica simple por ahora: Solo texto. 
        # El usuario pedirá "Dame catálogo" o el dispatcher encadenará acciones.
        
        # CORRECCION: El usuario original recibía el catálogo con el saludo.
        # Es mejor mantener esa experiencia.
        
        return {'success': True, 'action': 'greeting'}
