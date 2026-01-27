"""
Tests para WhatsAppService.
"""
import pytest
from unittest.mock import Mock, patch


# Mock de settings para evitar validación de Pydantic
mock_settings = Mock()
mock_settings.whatsapp_verify_token = "mi_token_secreto_verificacion"
mock_settings.whatsapp_access_token = "test_token"
mock_settings.whatsapp_phone_number_id = "123456"
mock_settings.whatsapp_api_version = "v18.0"
mock_settings.whatsapp_api_url = "https://graph.facebook.com"


@pytest.fixture
def whatsapp_service():
    """Crear instancia de WhatsAppService con settings mockeados."""
    with patch('src.infrastructure.external.whatsapp_service.settings', mock_settings):
        from src.infrastructure.external.whatsapp_service import WhatsAppService
        return WhatsAppService()


def test_verify_webhook_success(whatsapp_service):
    """Test: Verificación exitosa de webhook."""
    challenge = whatsapp_service.verify_webhook(
        mode="subscribe",
        token="mi_token_secreto_verificacion",
        challenge="test_challenge_123"
    )
    
    assert challenge == "test_challenge_123"


def test_verify_webhook_invalid_mode(whatsapp_service):
    """Test: Verificación falla con modo inválido."""
    challenge = whatsapp_service.verify_webhook(
        mode="invalid_mode",
        token="mi_token_secreto_verificacion",
        challenge="test_challenge_123"
    )
    
    assert challenge is None


def test_verify_webhook_invalid_token(whatsapp_service):
    """Test: Verificación falla con token inválido."""
    challenge = whatsapp_service.verify_webhook(
        mode="subscribe",
        token="token_incorrecto",
        challenge="test_challenge_123"
    )
    
    assert challenge is None


def test_extract_message_data_text_message(whatsapp_service):
    """Test: Extraer datos de mensaje de texto."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "id": "msg_123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {
                            "body": "Quiero 2 zapatos"
                        }
                    }]
                }
            }]
        }]
    }
    
    message_data = whatsapp_service.extract_message_data(webhook_data)
    
    assert message_data is not None
    assert message_data['from'] == "1234567890"
    assert message_data['message_id'] == "msg_123"
    assert message_data['text'] == "Quiero 2 zapatos"


def test_extract_message_data_non_text_message(whatsapp_service):
    """Test: Mensaje no texto retorna None."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "id": "msg_123",
                        "timestamp": "1234567890",
                        "type": "image"
                    }]
                }
            }]
        }]
    }
    
    message_data = whatsapp_service.extract_message_data(webhook_data)
    
    assert message_data is None


def test_extract_message_data_no_messages(whatsapp_service):
    """Test: Webhook sin mensajes retorna None."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": []
                }
            }]
        }]
    }
    
    message_data = whatsapp_service.extract_message_data(webhook_data)
    
    assert message_data is None


def test_format_quote_message(whatsapp_service):
    """Test: Formatear mensaje de cotización."""
    quote_data = {
        'items': [
            {
                'product_name': 'Zapatos',
                'quantity': 2,
                'unit_price': 45.99,
                'subtotal': 91.98
            },
            {
                'product_name': 'Camisa',
                'quantity': 1,
                'unit_price': 25.50,
                'subtotal': 25.50
            }
        ],
        'total': 117.48
    }
    
    message = whatsapp_service._format_quote_message(quote_data)
    
    assert "Cotización Generada" in message
    assert "Zapatos" in message
    assert "Camisa" in message
    assert "$117.48" in message
    assert "2 × $45.99 = $91.98" in message
