import requests
import json
import os
import sys

# Agregar el directorio raíz al path para poder importar módulos si fuera necesario, 
# aunque este script funcionará de forma independiente vía requests.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

WEBHOOK_URL = "http://127.0.0.1:8000/api/v1/webhook"

def simulate_whatsapp_message():
    # Payload simulando estructura real de WhatsApp Cloud API
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_PHONE_NUMBER_ID_MOCK",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "584121234567",
                                "phone_number_id": "123456789"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Cliente de Prueba"
                                    },
                                    "wa_id": "584121234567"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "584121234567",
                                    "id": "wamid.HBgLMjM0NTY3ODkwAA",
                                    "timestamp": "1706294340",
                                    "text": {
                                        "body": "Hola, quiero 5 laptops gamers"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    print(f"[INFO] Enviando mensaje simulado a {WEBHOOK_URL}...")
    print(f"[MSG]  Mensaje: 'Hola, quiero 3 pares de zapatos y 2 camisas por favor'")
    print("-" * 50)

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        
        print(f"[RECV] Respuesta Status: {response.status_code}")
        print(f"[RECV] Respuesta Body: {response.text}")
        
        if response.status_code == 200:
            print("\n[OK] PRUEBA EXITOSA: El webhook procesó el mensaje correctamente.")
        else:
            print("\n[FAIL] PRUEBA FALLIDA: El servidor rechazó o falló al procesar.")
            
    except requests.exceptions.ConnectionError:
        print(f"\n[ERR] ERROR DE CONEXIÓN: No se pudo conectar a {WEBHOOK_URL}. ¿Está corriendo el servidor?")

if __name__ == "__main__":
    simulate_whatsapp_message()
