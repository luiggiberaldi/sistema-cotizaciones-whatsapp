from typing import Dict, Optional, List
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService
from ....domain.services import QuoteService
from ....infrastructure.services.invoice_service import InvoiceService
from ....infrastructure.services.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)

class GreetingHandler(WhatsAppHandler):
    """
    Maneja los saludos iniciales y envía el catálogo.
    """
    
    def __init__(
        self, 
        whatsapp_service: WhatsAppService,
        quote_service: QuoteService,
        invoice_service: InvoiceService,
        storage_service: StorageService
    ):
        self.whatsapp_service = whatsapp_service
        self.quote_service = quote_service
        self.invoice_service = invoice_service
        self.storage_service = storage_service

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
        
        # 2. Enviar Catálogo PDF
        try:
            logger.info("Intentando enviar catálogo PDF en saludo...")
            
            # Obtener productos y generar catálogo
            products = self.quote_service.get_available_products()
            logger.info(f"Productos encontrados: {len(products) if products else 0}")
            
            if products:
                # Generamos el PDF (esto suele ser rápido o cacheado)
                catalog_path = self.invoice_service.generate_catalog_pdf(products)
                logger.info(f"PDF generado en: {catalog_path}")
                
                storage_path = f"catalogs/catalogo_actual.pdf"
                
                # Subir o actualizar catálogo (StorageService manejará si ya existe o lo sobreescribe)
                public_url = await self.storage_service.upload_pdf(catalog_path, storage_path)
                logger.info(f"URL pública del PDF: {public_url}")
                
                if public_url:
                    result = await self.whatsapp_service.send_document(
                        to=from_number,
                        link=public_url,
                        caption="Catálogo 2026",
                        filename="Catalogo_Productos_2026.pdf"
                    )
                    logger.info(f"Resultado envío PDF: {result}")
                else:
                    logger.error("No se obtuvo URL pública para el PDF.")
            else:
                logger.warning("No hay productos disponibles para generar el catálogo en el saludo.")
                
        except Exception as e:
            logger.error(f"Error CRÍTICO enviando catálogo en saludo: {e}", exc_info=True)
            
        return {'success': True, 'action': 'greeting'}
