import asyncio
import os
import sys

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.config.database import get_supabase_client
from src.infrastructure.database.product_repository import ProductRepository
from src.domain.entities.product import Product

async def seed_products():
    print("Iniciando carga de productos de ejemplo...")
    
    supabase = get_supabase_client()
    repo = ProductRepository(supabase)
    
    # 1. Limpiar base de datos actual (opcional, pero útil para resetear)
    print("Limpiando inventario actual...")
    all_products = repo.get_all()
    for p in all_products:
        repo.delete(p.id)
        
    # 2. Lista de productos con imágenes reales (URLs directas de stock o placeholders de alta calidad)
    products_data = [
        {
            "name": "Pantalón Blue Jeans",
            "price": 35.00,
            "category": "ropa",
            "image_url": "https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?auto=format&fit=crop&w=500&q=80",
            "aliases": ["pantalon", "jeans", "vaqueros", "bluejeans"]
        },
        {
            "name": "Cinturón de Cuero",
            "price": 20.00,
            "category": "accesorios",
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=500&q=80", 
            "aliases": ["cinturon", "correa", "belt"]
        },
        {
            "name": "Vestido Casual",
            "price": 48.00,
            "category": "ropa",
            "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=500&q=80",
            "aliases": ["vestido", "dress", "traje"]
        },
        {
            "name": "Corbata Elegante",
            "price": 18.00,
            "category": "accesorios",
            "image_url": "https://images.unsplash.com/photo-1589756823695-278bc70d6777?auto=format&fit=crop&w=500&q=80",
            "aliases": ["corbata", "tie", "lazo"]
        },
        {
            "name": "Zapatos Deportivos Blancos",
            "price": 45.99,
            "category": "calzado",
            "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=500&q=80",
            "aliases": ["zapatos", "tenis", "shoes", "zapatillas"]
        },
        {
            "name": "Camisa Blanca Hombre",
            "price": 25.50,
            "category": "ropa",
            "image_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?auto=format&fit=crop&w=500&q=80",
            "aliases": ["camisa", "shirt", "blusa"]
        },
        {
            "name": "Gorra Negra",
            "price": 15.00,
            "category": "accesorios",
            "image_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=500&q=80",
            "aliases": ["gorra", "cap", "visera"]
        },
        {
            "name": "Chaqueta Jean",
            "price": 55.00,
            "category": "ropa",
            "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=500&q=80",
            "aliases": ["chaqueta", "jacket", "abrigo"]
        },
        {
            "name": "Bolso de Mano",
            "price": 40.00,
            "category": "accesorios",
            "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=500&q=80",
            "aliases": ["bolso", "cartera", "bag"]
        },
        {
            "name": "Medias Tobilleras",
            "price": 8.00,
            "category": "ropa",
            "image_url": "https://images.unsplash.com/photo-1586350977771-b3b0abd50f82?auto=format&fit=crop&w=500&q=80",
            "aliases": ["medias", "calcetines", "socks"]
        }
    ]

    for p_data in products_data:
        try:
            prod = Product(**p_data)
            created = repo.create(prod)
            print(f"Creado: {created.name}")
        except Exception as e:
            print(f"Error creando {p_data['name']}: {e}")

    print("Carga completa. [OK]")

if __name__ == "__main__":
    asyncio.run(seed_products())
