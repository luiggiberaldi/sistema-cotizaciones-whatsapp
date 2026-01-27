"""
Tests para RetryQueue.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.infrastructure.external.retry_queue import RetryQueue, RetryMessage


@pytest.fixture
def temp_queue_file(tmp_path):
    """Crear archivo temporal para la cola."""
    return str(tmp_path / "test_queue.json")


@pytest.fixture
def retry_queue(temp_queue_file):
    """Crear instancia de RetryQueue."""
    return RetryQueue(queue_file=temp_queue_file)


def test_add_message_to_queue(retry_queue):
    """Test: Agregar mensaje a la cola."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message",
        max_attempts=5
    )
    
    assert retry_queue.get_queue_size() == 1


def test_get_messages_to_retry(retry_queue):
    """Test: Obtener mensajes listos para reintentar."""
    # Agregar mensaje con next_retry en el pasado
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message"
    )
    
    # Modificar next_retry para que sea en el pasado
    queue = retry_queue._load_queue()
    queue[0].next_retry = (datetime.now() - timedelta(minutes=5)).isoformat()
    retry_queue._save_queue(queue)
    
    messages = retry_queue.get_messages_to_retry()
    assert len(messages) == 1
    assert messages[0].id == "msg_123"


def test_update_message_attempt_success(retry_queue):
    """Test: Actualizar intento exitoso (remover de cola)."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message"
    )
    
    assert retry_queue.get_queue_size() == 1
    
    retry_queue.update_message_attempt(
        message_id="msg_123",
        success=True
    )
    
    assert retry_queue.get_queue_size() == 0


def test_update_message_attempt_failure(retry_queue):
    """Test: Actualizar intento fallido (incrementar intentos)."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message",
        max_attempts=3
    )
    
    retry_queue.update_message_attempt(
        message_id="msg_123",
        success=False,
        error="Connection timeout"
    )
    
    queue = retry_queue._load_queue()
    assert len(queue) == 1
    assert queue[0].attempts == 1
    assert queue[0].last_error == "Connection timeout"


def test_exponential_backoff(retry_queue):
    """Test: Backoff exponencial en reintentos."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message"
    )
    
    # Primer fallo: 2^1 = 2 minutos
    retry_queue.update_message_attempt("msg_123", success=False)
    queue = retry_queue._load_queue()
    next_retry_1 = datetime.fromisoformat(queue[0].next_retry)
    
    # Segundo fallo: 2^2 = 4 minutos
    retry_queue.update_message_attempt("msg_123", success=False)
    queue = retry_queue._load_queue()
    next_retry_2 = datetime.fromisoformat(queue[0].next_retry)
    
    # El segundo reintento debe ser más tarde que el primero
    assert next_retry_2 > next_retry_1


def test_get_failed_messages(retry_queue):
    """Test: Obtener mensajes que alcanzaron máximo de intentos."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message",
        max_attempts=2
    )
    
    # Fallar 2 veces
    retry_queue.update_message_attempt("msg_123", success=False)
    retry_queue.update_message_attempt("msg_123", success=False)
    
    failed = retry_queue.get_failed_messages()
    assert len(failed) == 1
    assert failed[0].id == "msg_123"
    assert failed[0].attempts == 2


def test_remove_message(retry_queue):
    """Test: Remover mensaje de la cola."""
    retry_queue.add_message(
        message_id="msg_123",
        to="1234567890",
        message="Test message"
    )
    
    assert retry_queue.get_queue_size() == 1
    
    retry_queue.remove_message("msg_123")
    
    assert retry_queue.get_queue_size() == 0


def test_clear_queue(retry_queue):
    """Test: Limpiar toda la cola."""
    retry_queue.add_message("msg_1", "123", "Test 1")
    retry_queue.add_message("msg_2", "456", "Test 2")
    retry_queue.add_message("msg_3", "789", "Test 3")
    
    assert retry_queue.get_queue_size() == 3
    
    retry_queue.clear_queue()
    
    assert retry_queue.get_queue_size() == 0


def test_duplicate_message_not_added(retry_queue):
    """Test: Mensaje duplicado no se agrega."""
    retry_queue.add_message("msg_123", "123", "Test")
    retry_queue.add_message("msg_123", "123", "Test")  # Duplicado
    
    assert retry_queue.get_queue_size() == 1
