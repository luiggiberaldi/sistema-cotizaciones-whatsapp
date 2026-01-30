from typing import Dict
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService
from ....domain.services import QuoteService
from ....infrastructure.services.invoice_service import InvoiceService
from ....infrastructure.services.storage_service import StorageService

class CatalogHandler(WhatsAppHandler):
    """
    Maneja la solicitud y envío del catálogo.
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
        
        # Obtener productos y generar catálogo
        products = self.quote_service.get_available_products()
        if products:
            catalog_path = self.invoice_service.generate_catalog_pdf(products)
            storage_path = f"catalogs/catalogo_actual.pdf"
            
            # Subir o actualizar catálogo
            public_url = await self.storage_service.upload_pdf(catalog_path, storage_path)
            
            if public_url:
                await self.whatsapp_service.send_message(from_number, "Aquí tienes nuestro catálogo actualizado 📂")
                await self.whatsapp_service.send_document(
                    to=from_number,
                    link=public_url,
                    caption="Catálogo 2026",
                    filename="Catalogo_Productos_2026.pdf"
                )
                return {'success': True, 'action': 'sent_catalog'}
        
        return {'success': False, 'reason': 'no_products_for_catalog'}
