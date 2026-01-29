"""
Servicio para interactuar con WhatsApp Cloud API.
"""
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime
from ..config.settings import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Servicio para enviar y recibir mensajes de WhatsApp Cloud API.
    
    Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api
    """
    
    def __init__(self):
        """Inicializar servicio de WhatsApp."""
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.api_version = settings.whatsapp_api_version
        self.base_url = f"{settings.whatsapp_api_url}/{self.api_version}"
        self.verify_token = settings.whatsapp_verify_token
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verificar webhook de WhatsApp.
        
        Meta envía una petición GET para verificar el webhook.
        
        Args:
            mode: Debe ser "subscribe"
            token: Token de verificación
            challenge: Challenge a retornar
            
        Returns:
            Challenge si la verificación es exitosa, None si falla
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verificado exitosamente")
            return challenge
        
        logger.warning(f"Verificación de webhook fallida: mode={mode}, token={token}")
        return None
    
    async def send_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Dict:
        """
        Enviar mensaje de texto a un número de WhatsApp.
        
        Args:
            to: Número de teléfono (formato internacional sin +)
            message: Texto del mensaje
            preview_url: Si debe mostrar preview de URLs
            
        Returns:
            Respuesta de la API
            
        Raises:
            httpx.HTTPError: Si la petición falla
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Mensaje enviado a {to}: {result}")
            return result
    
    async def send_quote_message(
        self,
        to: str,
        quote_data: Dict
    ) -> Dict:
        """
        Enviar cotización formateada como mensaje de WhatsApp.
        
        Args:
            to: Número de teléfono
            quote_data: Datos de la cotización
            
        Returns:
            Respuesta de la API
        """
        # Formatear mensaje de cotización
        message = self._format_quote_message(quote_data)
        
        return await self.send_message(to, message, preview_url=False)
    
    async def send_document(
        self,
        to: str,
        link: str,
        caption: Optional[str] = None
    ) -> Dict:
        """
        Enviar documento (PDF) por WhatsApp.
        
        Args:
            to: Número de teléfono
            link: URL pública del documento (PDF)
            caption: Texto opcional
            
        Returns:
            Respuesta de la API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": link,
                "caption": caption or ""
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Documento enviado a {to}: {result}")
            return result
            
    def _format_quote_message(self, quote_data: Dict) -> str:
        """
        Formatear cotización como mensaje de texto.
        
        Args:
            quote_data: Datos de la cotización
            
        Returns:
            Mensaje formateado
        """
        items = quote_data.get('items', [])
        total = quote_data.get('total', 0)
        
        # Encabezado
        message = "✅ *Cotización Generada*\n\n"
        
        # Items
        message += "📦 *Productos:*\n"
        for i, item in enumerate(items, 1):
            name = item.get('product_name', 'Producto')
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            subtotal = item.get('subtotal', 0)
            
            message += f"{i}. {name}\n"
            message += f"   Cantidad: {qty} × ${price:.2f} = ${subtotal:.2f}\n"
        
        # Total
        message += f"\n💰 *Total: ${total:.2f}*\n\n"
        
        # Footer
        message += "Tu cotización ha sido registrada. "
        message += "Te enviaremos el PDF oficial en unos instantes... ⏳"
        
        return message
    
    def extract_message_data(self, webhook_data: Dict) -> Optional[Dict]:
        """
        Extraer datos del mensaje desde el webhook de WhatsApp.
        
        Args:
            webhook_data: Datos del webhook
            
        Returns:
            Diccionario con from, message_id, timestamp, text
            o None si no es un mensaje de texto
        """
        try:
            entry = webhook_data.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            
            # Verificar que hay mensajes
            messages = value.get('messages', [])
            if not messages:
                return None
            
            message = messages[0]
            
            # Solo procesar mensajes de texto
            if message.get('type') != 'text':
                logger.info(f"Mensaje no es de texto: {message.get('type')}")
                return None
            
            # Intentar extraer nombre del contacto
            contacts = value.get('contacts', [])
            sender_name = None
            if contacts:
                sender_name = contacts[0].get('profile', {}).get('name')

            return {
                'from': message.get('from'),
                'name': sender_name,
                'message_id': message.get('id'),
                'timestamp': message.get('timestamp'),
                'text': message.get('text', {}).get('body', '')
            }
            
        except (IndexError, KeyError) as e:
            logger.error(f"Error extrayendo datos del mensaje: {e}")
            return None
    
    async def mark_message_as_read(self, message_id: str) -> Dict:
        """
        Marcar mensaje como leído.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Respuesta de la API
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "es",
        parameters: list = None
    ) -> Dict:
        """
        Enviar mensaje plantilla aprobado por Meta.
        
        Args:
            to: Número de teléfono (formato internacional sin +)
            template_name: Nombre del template aprobado
            language_code: Código de idioma (es, en, pt, etc.)
            parameters: Lista de parámetros para el template
            
        Returns:
            Respuesta de la API
            
        Raises:
            httpx.HTTPError: Si la petición falla
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Construir componentes del template
        components = []
        if parameters:
            components.append({
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(param)}
                    for param in parameters
                ]
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template enviado a {to}: {result}")
            return result
