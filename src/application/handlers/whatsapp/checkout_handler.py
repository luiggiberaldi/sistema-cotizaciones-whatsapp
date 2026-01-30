from typing import Dict, Optional, List
from datetime import datetime
import logging
from .base_handler import WhatsAppHandler
from ....infrastructure.external.whatsapp_service import WhatsAppService
from ....domain.services import QuoteService
from ....domain.repositories import QuoteRepository
from ....infrastructure.services.invoice_service import InvoiceService
from ....infrastructure.services.storage_service import StorageService
from ....infrastructure.database.customer_repository import CustomerRepository
from ....infrastructure.services.customer_service import CustomerService

logger = logging.getLogger(__name__)

class CheckoutHandler(WhatsAppHandler):
    """
    Maneja la confirmación del pedido (Checkout).
    Genera la cotización final, actualiza CRM y envía los documentos.
    """
    
    def __init__(
        self,
        whatsapp_service: WhatsAppService,
        quote_service: QuoteService,
        quote_repository: QuoteRepository,
        session_repository,
        invoice_service: InvoiceService,
        storage_service: StorageService,
        customer_repository: Optional[CustomerRepository] = None
    ):
        self.whatsapp_service = whatsapp_service
        self.quote_service = quote_service
        self.quote_repository = quote_repository
        self.session_repository = session_repository
        self.invoice_service = invoice_service
        self.storage_service = storage_service
        self.customer_repository = customer_repository

    async def handle(self, message_data: Dict) -> Dict:
        from_number = message_data.get('from')
        message_id = message_data.get('message_id')
        
        session = self.session_repository.get_session(from_number)
        if not session or not session.get('items'):
            await self.whatsapp_service.send_message(
                to=from_number,
                message="⚠️ No tienes una cotización activa para confirmar."
            )
            return {'success': False, 'reason': 'no_active_session'}

        client_data = session.get('client_data', {}) or {}
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
            
            # Inicializar notes si es None
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
            await self._generate_and_send_pdf(from_number, created_quote, quote_data)
            
            return {'success': True, 'action': 'checkout', 'quote_id': created_quote.id}

        except Exception as e:
            logger.error(f"Error en checkout: {e}")
            await self.whatsapp_service.send_message(to=from_number, message="❌ Error generando cotización final.")
            return {'success': False, 'error': str(e)}

    async def _generate_and_send_pdf(self, from_number, created_quote, quote_data):
        try:
            pdf_path = self.invoice_service.generate_invoice_pdf(quote_data)
            
            # Nombre de archivo único
            timestamp = int(datetime.now().timestamp())
            filename = f"quote_{created_quote.id}_{timestamp}.pdf"
            storage_path = f"quotes/{from_number}/{filename}"
            
            public_url = await self.storage_service.upload_pdf(pdf_path, storage_path)
            
            if public_url:
                # Sanitizar nombre para archivo
                safe_name = "".join(c if c.isalnum() else "_" for c in (created_quote.client_name or "Cliente"))
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
                await self.whatsapp_service.send_message(to=from_number, message="Se generó la cotización pero hubo un problema enviando el PDF.")
            
        except Exception as pdf_err:
            logger.error(f"Error generando/subiendo PDF: {pdf_err}")
            await self.whatsapp_service.send_message(to=from_number, message="Cotización guardada exitosamente. Hubo un error técnico generando el PDF.")

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
