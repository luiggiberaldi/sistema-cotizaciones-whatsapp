"""
Aplicación principal de FastAPI.
Punto de entrada del sistema de cotizaciones.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.config.settings import settings
from .infrastructure.api.routes import quote_router, generate_router, webhook_router, broadcast_router, product_router, business_info_routes, customer_router


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST para gestión de cotizaciones con Arquitectura Hexagonal",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Logging de configuración al inicio
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@app.on_event("startup")
async def startup_event():
    service_key = getattr(settings, 'supabase_service_key', "")
    is_service_key_set = "✅ SET" if service_key and len(service_key) > 10 else "❌ MISSING/EMPTY"
    
    logger.info("=== CONFIGURATION CHECK ===")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Supabase URL: {settings.supabase_url}")
    logger.info(f"Supabase Service Key: {is_service_key_set}")
    
    # Verificar credenciales de WhatsApp
    from .infrastructure.external.whatsapp_service import WhatsAppService
    ws = WhatsAppService()
    is_valid = await ws.check_credentials()
    status_icon = "✅" if is_valid else "❌"
    logger.info(f"WhatsApp Token Status: {status_icon} ({'Válido' if is_valid else 'INVÁLIDO'})")
    
    logger.info("===========================")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(quote_router, prefix=settings.api_v1_prefix)
app.include_router(generate_router, prefix=settings.api_v1_prefix)
app.include_router(webhook_router, prefix=settings.api_v1_prefix)
app.include_router(broadcast_router, prefix=settings.api_v1_prefix)
app.include_router(product_router, prefix=settings.api_v1_prefix)
app.include_router(business_info_routes.router, prefix=settings.api_v1_prefix)
app.include_router(customer_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
async def root():
    """Endpoint raíz para verificar que la API está funcionando."""
    return {
        "message": "Sistema de Cotizaciones API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/keep-alive", tags=["health"])
async def keep_alive():
    """Endpoint ligero para evitar modo suspensión (Cold Start)."""
    return {"status": "ok", "ping": "pong"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
