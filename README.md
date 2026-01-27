# Sistema Correlativo - API de Cotizaciones con WhatsApp

Sistema de generación de cotizaciones con procesamiento de lenguaje natural (NLP) e integración con WhatsApp Cloud API.

## 🚀 Características

- ✅ Generación de cotizaciones desde texto libre (NLP)
- ✅ Webhook de WhatsApp Cloud API
- ✅ Envío automático de respuestas
- ✅ Retry pattern con backoff exponencial
- ✅ Frontend React con Tailwind CSS
- ✅ Listas de difusión de WhatsApp
- ✅ Arquitectura hexagonal
- ✅ Tests automatizados (pytest)

## 📋 Requisitos

- Python 3.12+
- PostgreSQL (Supabase)
- Node.js 18+ (para frontend)
- Cuenta de WhatsApp Business API

## 🔧 Instalación Local

### Backend

```bash
# Clonar repositorio
git clone <repo-url>
cd sistema-correlativo

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar servidor
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentación

- [Guía Rápida](GUIA_RAPIDA.md)
- [Webhook de WhatsApp](docs/WHATSAPP_WEBHOOK.md)
- [Despliegue en Render](docs/DEPLOY.md)
- [Frontend React](frontend/README.md)

## 🌐 Despliegue

### Producción

**Backend**: Render (con `render.yaml`)  
**Frontend**: Vercel (con `vercel.json`)

Ver [DEPLOY_PRODUCTION.md](DEPLOY_PRODUCTION.md) para guía rápida.

**Documentación detallada**:
- [Backend en Render](docs/DEPLOY.md)
- [Frontend en Vercel](frontend/DEPLOY_VERCEL.md)

### Render (Backend)

Este proyecto está configurado para despliegue automático en Render usando `render.yaml`.

Ver [docs/DEPLOY.md](docs/DEPLOY.md) para instrucciones detalladas.

**Inicio rápido**:
1. Conectar repositorio en [Render](https://dashboard.render.com)
2. Configurar variables de entorno
3. Deploy automático ✅

### Vercel (Frontend)

El frontend se despliega en Vercel con configuración en `frontend/vercel.json`.

**Inicio rápido**:
1. Conectar repositorio en [Vercel](https://vercel.com)
2. Root Directory: `frontend`
3. Variable: `VITE_API_URL=https://tu-backend.onrender.com/api/v1`
4. Deploy ✅

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Tests específicos
pytest tests/test_quote_service.py
pytest tests/test_whatsapp_service.py
pytest tests/test_retry_queue.py

# Con cobertura
pytest --cov=src tests/
```

## 📡 API Endpoints

### Cotizaciones
- `POST /api/v1/generate/quote-from-text` - Generar cotización desde texto
- `GET /api/v1/generate/products` - Listar productos
- `POST /api/v1/generate/search-product` - Buscar producto

### Webhook WhatsApp
- `GET /api/v1/webhook` - Verificar webhook
- `POST /api/v1/webhook` - Recibir mensajes
- `POST /api/v1/webhook/retry` - Reintentar mensajes fallidos
- `GET /api/v1/webhook/queue-status` - Estado de cola

### Broadcast
- `POST /api/v1/broadcast/send-template` - Enviar template a múltiples clientes
- `GET /api/v1/broadcast/templates` - Listar templates disponibles

## 🏗️ Arquitectura

```
src/
├── domain/              # Entidades y lógica de negocio
├── application/         # Casos de uso
└── infrastructure/      # Implementaciones
    ├── api/            # Rutas FastAPI
    ├── config/         # Configuración
    ├── database/       # Repositorios
    └── external/       # Servicios externos (WhatsApp)
```

## 🔐 Variables de Entorno

Ver `.env.example` para todas las variables requeridas.

**Críticas**:
- `SUPABASE_URL` - URL de Supabase
- `SUPABASE_KEY` - API Key de Supabase
- `SECRET_KEY` - Clave secreta para JWT
- `WHATSAPP_VERIFY_TOKEN` - Token de verificación
- `WHATSAPP_ACCESS_TOKEN` - Token de acceso de WhatsApp
- `WHATSAPP_PHONE_NUMBER_ID` - ID del número de WhatsApp

## 📄 Licencia

MIT

## 👥 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📞 Soporte

Para preguntas o soporte, abrir un issue en GitHub.
