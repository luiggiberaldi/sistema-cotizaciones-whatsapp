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
            self.model_name = "mixtral-8x7b-32768" # Modelo rápido y eficiente en Groq
            logger.info(f"GroqService: Initialized with model {self.model_name}")
            
        except Exception as e:
            logger.error(f"GroqService: Initialization failed: {e}", exc_info=True)
            self.client = None

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
            
            from groq import AsyncGroq
            async_client = AsyncGroq(api_key=self.api_key)
            
            completion = await async_client.chat.completions.create(
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
