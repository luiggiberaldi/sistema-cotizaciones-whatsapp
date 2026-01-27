# Webhook de WhatsApp Cloud API

## 📱 Descripción

Implementación completa de webhook para **WhatsApp Cloud API** con:
- ✅ Verificación de token de seguridad de Meta
- ✅ Procesamiento automático de mensajes
- ✅ Integración con QuoteService (NLP)
- ✅ Envío automático de respuestas
- ✅ **Retry Pattern** con cola de reintentos
- ✅ Backoff exponencial
- ✅ Manejo robusto de errores

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│      WhatsApp Cloud API (Meta)          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   GET /webhook (Verificación)           │
│   POST /webhook (Recibir mensajes)      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   ProcessWhatsAppMessageUseCase         │
│   - Extraer texto del mensaje           │
│   - Generar cotización (QuoteService)   │
│   - Enviar respuesta automática         │
│   - Si falla → Cola de reintentos       │
└──────────────┬──────────────────────────┘
               │
               ├──────────────┐
               ▼              ▼
┌──────────────────┐  ┌──────────────────┐
│  WhatsAppService │  │   RetryQueue     │
│  - send_message  │  │  - add_message   │
│  - verify_webhook│  │  - retry logic   │
└──────────────────┘  └──────────────────┘
```

## 🔧 Componentes

### 1. WhatsAppService

**Archivo**: `src/infrastructure/external/whatsapp_service.py`

**Métodos principales**:
```python
verify_webhook(mode, token, challenge)  # Verificar webhook
send_message(to, message)               # Enviar mensaje de texto
send_quote_message(to, quote_data)      # Enviar cotización formateada
extract_message_data(webhook_data)      # Extraer datos del webhook
mark_message_as_read(message_id)        # Marcar como leído
```

### 2. RetryQueue

**Archivo**: `src/infrastructure/external/retry_queue.py`

**Características**:
- Cola persistente en JSON
- Backoff exponencial: 1min, 2min, 4min, 8min, 16min
- Máximo 5 intentos por defecto
- Tracking de errores

**Métodos principales**:
```python
add_message(message_id, to, message, ...)  # Agregar a cola
get_messages_to_retry()                     # Obtener mensajes listos
update_message_attempt(message_id, success) # Actualizar intento
get_failed_messages()                       # Mensajes fallidos
```

### 3. ProcessWhatsAppMessageUseCase

**Archivo**: `src/application/use_cases/whatsapp_use_cases.py`

**Flujo**:
1. Recibir mensaje de WhatsApp
2. Extraer texto
3. Generar cotización con QuoteService
4. Enviar respuesta automática
5. Si falla → Agregar a cola de reintentos

## 📡 Endpoints

### 1. Verificar Webhook (GET)

**Endpoint**: `GET /api/v1/webhook`

**Parámetros**:
- `hub.mode` = "subscribe"
- `hub.verify_token` = tu token secreto
- `hub.challenge` = challenge de Meta

**Ejemplo**:
```
GET /api/v1/webhook?hub.mode=subscribe&hub.verify_token=mi_token_secreto_verificacion&hub.challenge=123456
```

**Respuesta exitosa**: `123456` (el challenge)

### 2. Recibir Mensajes (POST)

**Endpoint**: `POST /api/v1/webhook`

**Body** (enviado por Meta):
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "1234567890",
          "id": "msg_123",
          "timestamp": "1234567890",
          "type": "text",
          "text": {
            "body": "Quiero 2 zapatos y 1 camisa"
          }
        }]
      }
    }]
  }]
}
```

**Respuesta**:
```json
{
  "status": "ok",
  "result": {
    "success": true,
    "quote": {...},
    "confidence_scores": [...],
    "sent": true
  }
}
```

### 3. Reintentar Mensajes Fallidos

**Endpoint**: `POST /api/v1/webhook/retry`

**Descripción**: Reintenta manualmente mensajes en cola

**Respuesta**:
```json
{
  "status": "ok",
  "result": {
    "messages_retried": 3,
    "successful": 2,
    "failed": 1
  }
}
```

### 4. Estado de la Cola

**Endpoint**: `GET /api/v1/webhook/queue-status`

**Respuesta**:
```json
{
  "queue_size": 5,
  "pending_retry": 2,
  "failed": 1,
  "failed_messages": [
    {
      "id": "retry_msg_123",
      "to": "1234567890",
      "attempts": 5,
      "last_error": "Connection timeout"
    }
  ]
}
```

## 🔐 Configuración

### Variables de Entorno

Agregar en `.env`:

```bash
# WhatsApp Cloud API
WHATSAPP_VERIFY_TOKEN=mi_token_secreto_verificacion
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_API_VERSION=v18.0
WHATSAPP_API_URL=https://graph.facebook.com
```

### Obtener Credenciales

1. **Crear App en Meta**: https://developers.facebook.com/
2. **Agregar WhatsApp Product**
3. **Obtener Access Token** (temporal o permanente)
4. **Obtener Phone Number ID**
5. **Configurar Webhook URL**: `https://tu-dominio.com/api/v1/webhook`

## 🔄 Patrón de Reintentos

### Backoff Exponencial

```
Intento 1: Inmediato (falla)
Intento 2: +2 minutos
Intento 3: +4 minutos
Intento 4: +8 minutos
Intento 5: +16 minutos
Máximo: 5 intentos → Marcar como fallido
```

### Ejemplo de Flujo

```
1. Usuario envía: "Quiero 2 zapatos"
2. Webhook recibe mensaje
3. QuoteService genera cotización
4. Intenta enviar respuesta → FALLA (timeout)
5. Agrega a RetryQueue
6. Espera 2 minutos
7. Reintenta → FALLA
8. Espera 4 minutos
9. Reintenta → ÉXITO
10. Remueve de cola
```

## 💬 Formato de Respuesta

Cuando se genera una cotización, el bot responde:

```
✅ *Cotización Generada*

📦 *Productos:*
1. Zapatos
   Cantidad: 2 × $45.99 = $91.98
2. Camisa
   Cantidad: 1 × $25.50 = $25.50

💰 *Total: $117.48*

¿Deseas confirmar esta cotización? Responde *SÍ* o *NO*
```

## 🧪 Tests

### Ejecutar Tests

```bash
# Tests de RetryQueue
python -m pytest tests/test_retry_queue.py -v

# Tests de WhatsAppService
python -m pytest tests/test_whatsapp_service.py -v

# Todos los tests
python -m pytest tests/ -v
```

### Cobertura de Tests

**RetryQueue** (11 tests):
- ✅ Agregar mensaje a cola
- ✅ Obtener mensajes listos para reintentar
- ✅ Actualizar intento exitoso
- ✅ Actualizar intento fallido
- ✅ Backoff exponencial
- ✅ Mensajes fallidos (max attempts)
- ✅ Remover mensaje
- ✅ Limpiar cola
- ✅ Duplicados no se agregan

**WhatsAppService** (7 tests):
- ✅ Verificación exitosa de webhook
- ✅ Verificación falla (modo inválido)
- ✅ Verificación falla (token inválido)
- ✅ Extraer datos de mensaje de texto
- ✅ Mensaje no-texto retorna None
- ✅ Webhook sin mensajes retorna None
- ✅ Formatear mensaje de cotización

## 🚀 Despliegue

### 1. Configurar Webhook en Meta

```bash
curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/subscribed_apps" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d "subscribed_fields=messages"
```

### 2. Exponer Endpoint Público

Opciones:
- **ngrok**: `ngrok http 8000`
- **Heroku**: Deploy directo
- **Railway**: Deploy con GitHub
- **VPS**: Nginx + Gunicorn

### 3. Configurar Cron Job para Reintentos

```bash
# Cada minuto
* * * * * curl -X POST http://localhost:8000/api/v1/webhook/retry
```

O usar **APScheduler** en Python:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    retry_messages_use_case.execute,
    'interval',
    minutes=1
)
scheduler.start()
```

## 🛡️ Manejo de Errores

### Errores Manejados

1. **Timeout de API**
   - → Agregar a cola de reintentos
   - → Backoff exponencial

2. **Token inválido**
   - → Log de error
   - → Retornar 403

3. **Mensaje no válido**
   - → Enviar mensaje de error al usuario
   - → No agregar a cola

4. **Error de parsing**
   - → Enviar instrucciones al usuario
   - → Log de warning

5. **Máximo de intentos alcanzado**
   - → Marcar como fallido
   - → Notificar administrador (TODO)

### Logs

```python
import logging

logger = logging.getLogger(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📊 Monitoreo

### Métricas Importantes

1. **Cola de reintentos**
   - Tamaño actual
   - Mensajes pendientes
   - Mensajes fallidos

2. **Tasa de éxito**
   - Mensajes enviados exitosamente
   - Mensajes fallidos
   - Promedio de intentos

3. **Latencia**
   - Tiempo de procesamiento
   - Tiempo de respuesta de API

### Dashboard Sugerido

```
GET /api/v1/webhook/queue-status

{
  "queue_size": 5,
  "pending_retry": 2,
  "failed": 1,
  "success_rate": 0.95,
  "avg_attempts": 1.2
}
```

## 🔒 Seguridad

### Mejores Prácticas

1. **Verificar firma de Meta** (TODO)
   ```python
   def verify_signature(payload, signature):
       # Verificar X-Hub-Signature-256
       pass
   ```

2. **Rate limiting**
   ```python
   from fastapi_limiter import FastAPILimiter
   
   @router.post("/webhook")
   @limiter.limit("100/minute")
   async def receive_webhook(...):
       pass
   ```

3. **Validar números de teléfono**
   ```python
   import phonenumbers
   
   def validate_phone(number):
       try:
           parsed = phonenumbers.parse(number)
           return phonenumbers.is_valid_number(parsed)
       except:
           return False
   ```

## 🎯 Próximas Mejoras

1. **Verificación de firma de Meta**
2. **Soporte para mensajes multimedia**
3. **Botones interactivos**
4. **Templates de mensajes**
5. **Dashboard de monitoreo**
6. **Notificaciones de mensajes fallidos**
7. **Análisis de conversaciones**
8. **Integración con CRM**
