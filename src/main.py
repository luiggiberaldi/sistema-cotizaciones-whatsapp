"""
Aplicación principal de FastAPI.
Punto de entrada del sistema de cotizaciones.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.config.settings import settings
from .infrastructure.api.routes import quote_router, generate_router, webhook_router, broadcast_router


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST para gestión de cotizaciones con Arquitectura Hexagonal",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(quote_router, prefix=settings.api_v1_prefix)
app.include_router(generate_router, prefix=settings.api_v1_prefix)
app.include_router(webhook_router, prefix=settings.api_v1_prefix)
app.include_router(broadcast_router, prefix=settings.api_v1_prefix)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
