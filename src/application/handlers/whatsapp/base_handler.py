from abc import ABC, abstractmethod
from typing import Dict, Any

class WhatsAppHandler(ABC):
    """
    Clase base abstracta para manejadores de intenciones de WhatsApp.
    """
    
    @abstractmethod
    async def handle(self, message_data: Dict) -> Dict:
        """
        Procesa el mensaje y retorna el resultado.
        
        Args:
            message_data: Diccionario con los datos del mensaje (from, text, name, etc.)
            
        Returns:
            Dict con el resultado de la operación (success, action, etc.)
        """
        pass
