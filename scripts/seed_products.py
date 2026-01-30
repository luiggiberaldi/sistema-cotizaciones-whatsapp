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
            "image_url": "https://img.freepik.com/foto-gratis/jeans-pantalon_1203-4522.jpg",
            "aliases": ["pantalon", "jeans", "vaqueros", "bluejeans"]
        },
        {
            "name": "Cinturón de Cuero",
            "price": 20.00,
            "category": "accesorios",
            "image_url": "https://img.freepik.com/foto-gratis/cinturon-cuero_1203-8134.jpg", 
            "aliases": ["cinturon", "correa", "belt"]
        },
        {
            "name": "Vestido Casual",
            "price": 48.00,
            "category": "ropa",
            "image_url": "https://img.freepik.com/foto-gratis/mujer-joven-hermosa-vestido-rojo_1303-17505.jpg",
            "aliases": ["vestido", "dress", "traje"]
        },
        {
            "name": "Corbata Elegante",
            "price": 18.00,
            "category": "accesorios",
            "image_url": "https://img.freepik.com/foto-gratis/corbata-azul_1203-8147.jpg",
            "aliases": ["corbata", "tie", "lazo"]
        },
        {
            "name": "Zapatos Deportivos Blancos",
            "price": 45.99,
            "category": "calzado",
            "image_url": "https://img.freepik.com/foto-gratis/zapatillas-blancas-aisladas-sobre-fondo-blanco_2831-29.jpg",
            "aliases": ["zapatos", "tenis", "shoes", "zapatillas"]
        },
        {
            "name": "Camisa Blanca Hombre",
            "price": 25.50,
            "category": "ropa",
            "image_url": "https://img.freepik.com/foto-gratis/camisa-blanca_1203-8186.jpg",
            "aliases": ["camisa", "shirt", "blusa"]
        },
        {
            "name": "Gorra Negra",
            "price": 15.00,
            "category": "accesorios",
            "image_url": "https://img.freepik.com/foto-gratis/gorra-negra-aislada_125540-1065.jpg",
            "aliases": ["gorra", "cap", "visera"]
        },
        {
            "name": "Chaqueta Jean",
            "price": 55.00,
            "category": "ropa",
            "image_url": "https://img.freepik.com/foto-gratis/chaqueta-mezclilla-azul_125540-580.jpg",
            "aliases": ["chaqueta", "jacket", "abrigo"]
        },
        {
            "name": "Bolso de Mano",
            "price": 40.00,
            "category": "accesorios",
            "image_url": "https://img.freepik.com/foto-gratis/bolso-cuero-mujer-aislado-blanco_2831-2.jpg",
            "aliases": ["bolso", "cartera", "bag"]
        },
        {
            "name": "Medias Tobilleras",
            "price": 8.00,
            "category": "ropa",
            "image_url": "https://img.freepik.com/foto-gratis/calcetines-blancos-cortos_125540-692.jpg",
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
