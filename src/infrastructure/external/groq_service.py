import json
from typing import List, Dict, Optional
from groq import Groq
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

class GroqService:
    """
    Servicio para interactuar con Groq AI como inteligencia de respaldo.
    Reemplaza a GeminiService.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GroqService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        try:
            self.api_key = settings.groq_api_key
            if not self.api_key:
                logger.warning("GroqService: No API Key configured.")
                self.client = None
                return

            self.client = Groq(api_key=self.api_key)
            # Pre-load async client lazy or here if preferred, but let's keep lazy for async loop safety
            self.async_client = None 
            self.model_name = "mixtral-8x7b-32768" # Modelo rápido y eficiente en Groq
            logger.info(f"GroqService: Initialized with model {self.model_name}")
            
        except Exception as e:
            logger.error(f"GroqService: Initialization failed: {e}", exc_info=True)
            self.client = None

    async def identify_products(self, user_message: str, catalog: List[Dict]) -> List[Dict]:
        """
        Usa IA para identificar productos y cantidades del catálogo basándose en el mensaje.
        Útil cuando el parser de regex falla por mala ortografía o gramática compleja.
        """
        if not self.async_client:
            from groq import AsyncGroq
            self.async_client = AsyncGroq(api_key=self.api_key)

        # Simplificar catálogo para el prompt
        simplified_catalog = [
            {"name": p['name'], "aliases": p.get('aliases', []), "category": p.get('category')}
            for p in catalog
        ]

        system_prompt = (
            "Eres un experto en identificar productos de un catálogo basándote en mensajes de clientes. "
            "Tu tarea es extraer qué productos quiere el cliente y en qué cantidad.\n\n"
            f"CATÁLOGO DISPONIBLE:\n{json.dumps(simplified_catalog, ensure_ascii=False)}\n\n"
            "REGLAS:\n"
            "1. Responde ÚNICAMENTE con un JSON (lista de objetos).\n"
            "2. Cada objeto debe tener: 'product_name' (el nombre EXACTO del catálogo) y 'quantity' (número entero).\n"
            "3. Si no encuentras un producto parecido en el catálogo, no lo incluyas.\n"
            "4. Si no se especifica cantidad, asume 1.\n"
            "5. NO incluyas explicaciones ni texto adicional."
        )

        try:
            completion = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1, # Baja temperatura para mayor fidelidad JSON
                max_tokens=500,
                response_format={"type": "json_object"} if "mixtral" not in self.model_name else None
            )
            
            content = completion.choices[0].message.content
            logger.info(f"Groq AI Identification Raw: {content}")
            
            # Limpiar posibles bloques de código markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            # Manejar si el modelo devuelve un objeto envuelto {"products": [...]}
            if isinstance(data, dict):
                for key in ['products', 'items', 'order']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # Si es un solo objeto no envuelto en lista
                if 'product_name' in data:
                    return [data]
                return []
            
            return data if isinstance(data, list) else []

        except Exception as e:
            logger.error(f"Error en Groq identify_products: {e}")
            return []

    async def get_fallback_response(self, user_message: str) -> str:
        """
        Obtiene respuesta de Groq para mensajes no entendidos.
        """
        if not self.client:
            logger.warning("GroqService: Client not available.")
            return "Lo siento, no puedo procesar tu solicitud en este momento (IA no disponible)."

        try:
            # System Prompt
            system_prompt = (
                "Eres un asistente de ventas amable y conciso. "
                "Tu función es responder preguntas generales sobre la tienda o redirigir al cliente "
                "si no entiendes su intención. Si te preguntan por productos, sugiere ver el catálogo. "
                "Responde en español de forma natural y breve (máximo 2 párrafos)."
            )
            
            logger.info(f"GroqService: Sending request for message '{user_message[:20]}...'")
            
            # Groq Python Client es síncrono por defecto, pero FastAPI maneja threads.
            # Para async nativo se requiere AsyncGroq, pero por ahora usaremos el cliente estándar
            # envuelto si es necesario, o confiamos en el thread pool de FastAPI.
            # Sin embargo, para no bloquear el event loop, lo ideal es usar AsyncGroqclient.
            # Vamos a usar AsyncGroq mejor.
            
            # Usar cliente asíncrono pre-inicializado
            if not self.async_client:
                 from groq import AsyncGroq
                 self.async_client = AsyncGroq(api_key=self.api_key)

            completion = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            response_text = completion.choices[0].message.content
            
            if response_text:
                logger.info("GroqService: Received successful response.")
                return response_text
            else:
                logger.warning("GroqService: Received empty response.")
                return "Disculpa, no pude generar una respuesta."

        except Exception as e:
            logger.error(f"GroqService: Error calling API: {e}", exc_info=True)
            return "Disculpa, tuve un problema de conexión. ¿Podrías repetirlo?"
