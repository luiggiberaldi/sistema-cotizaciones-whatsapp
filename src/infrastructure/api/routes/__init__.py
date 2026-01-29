"""Rutas de la API."""
from .quote_routes import router as quote_router
from .generate_routes import router as generate_router
from .webhook_routes import router as webhook_router
from .broadcast_routes import router as broadcast_router
from .product_routes import router as product_router

__all__ = ['quote_router', 'generate_router', 'webhook_router', 'broadcast_router', 'product_router']
