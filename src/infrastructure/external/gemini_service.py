import google.generativeai as genai
from datetime import datetime
import time
from ...config.settings import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Servicio para interactuar con Gemini AI como inteligencia de respaldo.
    Incluye Rate Limiter simple (50 requests/min).
    """
    
    _instance = None
    _request_count = 0
    _last_reset_time = time.time()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializar lista de claves de Gemini y modelo."""
        # Recolectar claves disponibles
        self.api_keys = []
        if settings.gemini_api_key:
            self.api_keys.append(settings.gemini_api_key)
        if settings.gemini_api_key_2:
            self.api_keys.append(settings.gemini_api_key_2)
            
        if not self.api_keys:
            self.model = None
            self.current_key_index = 0
            logger.warning("Gemini API Key no configurada.")
            return

        from itertools import cycle
        self.key_cycle = cycle(self.api_keys)
        self.current_key_index = 0
        
        # Configuración inicial (se actualizará en cada request para round robin)
        # Configuración de modelo: Usando gemini-2.5-flash como solicitado (Alta velocidad, bajo costo, contexto 1M)
        self.model_name = "gemini-2.5-flash"
        # Pre-instanciamos modelo, pero la key se configura globalmente antes de usar
        self.model = genai.GenerativeModel(self.model_name)

    def _rotate_key(self):
        """Rotar a la siguiente API Key disponible."""
        if not self.api_keys:
            return
            
        next_key = next(self.key_cycle)
        # Re-configurar la librería globalmente con la nueva clave
        genai.configure(api_key=next_key)
        
        # Log para debug (ocultando parte de la clave)
        key_masked = f"{next_key[:4]}...{next_key[-4:]}" if len(next_key) > 8 else "***"
        logger.info(f"Usando Gemini Key: {key_masked}")

    def _check_rate_limit(self) -> bool:
        """
        Verifica si se ha excedido el límite de 50 peticiones por minuto.
        Reinicia el contador cada 60 segundos.
        """
        current_time = time.time()
        
        # Reiniciar contador si pasó 1 minuto
        if current_time - self._last_reset_time > 60:
            self._request_count = 0
            self._last_reset_time = current_time
            
        if self._request_count >= 50:
            logger.warning("Rate Limit de Gemini excedido (50 req/min).")
            return False
            
        self._request_count += 1
        return True

    async def get_fallback_response(self, user_message: str) -> str:
        """
        Obtiene respuesta de Gemini para mensajes no entendidos.
        Usa Round Robin de API Keys.
        """
        if not self.model or not self.api_keys:
            return "Lo siento, no puedo procesar tu solicitud en este momento."

        if not self._check_rate_limit():
            return "Lo siento, estoy recibiendo demasiadas consultas. Por favor intenta en un minuto."

        try:
            # 1. Rotar Key antes de la llamada
            self._rotate_key()
            
            # System Prompt
            system_prompt = (
                "Eres un asistente de ventas de una tienda. "
                "Tu única función es responder preguntas generales o redirigir al usuario al proceso de cotización "
                "si no entiendes su pregunta. Si no sabes la respuesta, pide amablemente que reformulen la pregunta, "
                "sin dar un error. Sé conciso y amable."
            )
            
            # Construir prompt completo
            full_prompt = f"{system_prompt}\n\nUsuario: {user_message}\nAsistente:"
            
            # Llamada síncrona envuelta
            response = await self.model.generate_content_async(full_prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error consultando Gemini: {e}")
            # Opcional: Reintentar con otra key si es error de cuota (429), pero por ahora simple rotacion
            return "Disculpa, no pude entender eso. ¿Podrías repetirlo?"
