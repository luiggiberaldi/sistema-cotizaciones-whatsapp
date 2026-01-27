"""
Cola de reintentos para mensajes fallidos (Retry Pattern).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RetryMessage:
    """Mensaje en cola de reintentos."""
    
    id: str
    to: str
    message: str
    quote_data: Optional[Dict]
    attempts: int
    max_attempts: int
    next_retry: str  # ISO format
    created_at: str
    last_error: Optional[str] = None


class RetryQueue:
    """
    Cola de reintentos para mensajes fallidos.
    
    Implementa el patrón Retry con backoff exponencial.
    """
    
    def __init__(self, queue_file: Optional[str] = None):
        """
        Inicializar cola de reintentos.
        
        Args:
            queue_file: Ruta al archivo de cola (JSON)
        """
        if queue_file is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            queue_file = base_dir / "data" / "retry_queue.json"
        
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo si no existe
        if not self.queue_file.exists():
            self._save_queue([])
    
    def _load_queue(self) -> List[RetryMessage]:
        """Cargar cola desde archivo."""
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [RetryMessage(**item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_queue(self, queue: List[RetryMessage]):
        """Guardar cola en archivo."""
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            data = [asdict(msg) for msg in queue]
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_message(
        self,
        message_id: str,
        to: str,
        message: str,
        quote_data: Optional[Dict] = None,
        max_attempts: int = 5,
        error: Optional[str] = None
    ):
        """
        Agregar mensaje a la cola de reintentos.
        
        Args:
            message_id: ID único del mensaje
            to: Número de teléfono destino
            message: Texto del mensaje
            quote_data: Datos de cotización (opcional)
            max_attempts: Máximo número de reintentos
            error: Error que causó el fallo
        """
        queue = self._load_queue()
        
        # Verificar si ya existe
        existing = next((m for m in queue if m.id == message_id), None)
        if existing:
            logger.warning(f"Mensaje {message_id} ya está en cola")
            return
        
        # Calcular próximo reintento (1 minuto)
        next_retry = datetime.now() + timedelta(minutes=1)
        
        retry_msg = RetryMessage(
            id=message_id,
            to=to,
            message=message,
            quote_data=quote_data,
            attempts=0,
            max_attempts=max_attempts,
            next_retry=next_retry.isoformat(),
            created_at=datetime.now().isoformat(),
            last_error=error
        )
        
        queue.append(retry_msg)
        self._save_queue(queue)
        
        logger.info(f"Mensaje {message_id} agregado a cola de reintentos")
    
    def get_messages_to_retry(self) -> List[RetryMessage]:
        """
        Obtener mensajes listos para reintentar.
        
        Returns:
            Lista de mensajes cuyo next_retry ya pasó
        """
        queue = self._load_queue()
        now = datetime.now()
        
        messages_to_retry = []
        for msg in queue:
            next_retry = datetime.fromisoformat(msg.next_retry)
            if now >= next_retry and msg.attempts < msg.max_attempts:
                messages_to_retry.append(msg)
        
        return messages_to_retry
    
    def update_message_attempt(
        self,
        message_id: str,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Actualizar intento de mensaje.
        
        Args:
            message_id: ID del mensaje
            success: Si el intento fue exitoso
            error: Error si falló
        """
        queue = self._load_queue()
        
        for i, msg in enumerate(queue):
            if msg.id == message_id:
                if success:
                    # Remover de la cola
                    queue.pop(i)
                    logger.info(f"Mensaje {message_id} enviado exitosamente, removido de cola")
                else:
                    # Incrementar intentos y calcular próximo reintento
                    msg.attempts += 1
                    msg.last_error = error
                    
                    # Backoff exponencial: 1min, 2min, 4min, 8min, 16min
                    backoff_minutes = 2 ** msg.attempts
                    next_retry = datetime.now() + timedelta(minutes=backoff_minutes)
                    msg.next_retry = next_retry.isoformat()
                    
                    queue[i] = msg
                    
                    if msg.attempts >= msg.max_attempts:
                        logger.error(
                            f"Mensaje {message_id} alcanzó máximo de intentos ({msg.max_attempts})"
                        )
                    else:
                        logger.warning(
                            f"Mensaje {message_id} falló (intento {msg.attempts}/{msg.max_attempts}), "
                            f"próximo reintento en {backoff_minutes} minutos"
                        )
                
                self._save_queue(queue)
                break
    
    def get_failed_messages(self) -> List[RetryMessage]:
        """
        Obtener mensajes que alcanzaron el máximo de intentos.
        
        Returns:
            Lista de mensajes fallidos
        """
        queue = self._load_queue()
        return [msg for msg in queue if msg.attempts >= msg.max_attempts]
    
    def remove_message(self, message_id: str):
        """Remover mensaje de la cola."""
        queue = self._load_queue()
        queue = [msg for msg in queue if msg.id != message_id]
        self._save_queue(queue)
        logger.info(f"Mensaje {message_id} removido de cola")
    
    def get_queue_size(self) -> int:
        """Obtener tamaño de la cola."""
        return len(self._load_queue())
    
    def clear_queue(self):
        """Limpiar toda la cola."""
        self._save_queue([])
        logger.info("Cola de reintentos limpiada")
