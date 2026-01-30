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
            "image_url": "https://sydney.pe/wp-content/uploads/2023/09/4pantalon-C-.jpg",
            "aliases": ["pantalon", "jeans", "vaqueros", "bluejeans"]
        },
        {
            "name": "Cinturón de Cuero",
            "price": 20.00,
            "category": "accesorios",
            "image_url": "https://www.calzadosinglese.com/cdn/shop/files/CI04_NEGRO.jpg?v=1734485068&width=1920", 
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
            "image_url": "https://media.istockphoto.com/id/157180004/es/foto/corbata-roja-sobre-blanco.jpg?s=612x612&w=0&k=20&c=RMd6X-Ff0DuEoE9wWC0NW6330ZXhXRyh83hPSyK4Jfk=",
            "aliases": ["corbata", "tie", "lazo"]
        },
        {
            "name": "Zapatos Deportivos Blancos",
            "price": 45.99,
            "category": "calzado",
            "image_url": "https://cdn.shopify.com/s/files/1/0269/9388/5267/files/STEVEMADDEN_SHOES_BIONIC2_WHITEACTIONLEATHER_SIDE.jpg?width=354&v=1744054625",
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
            "image_url": "https://i.pinimg.com/736x/9b/56/e7/9b56e7696cc8903d16b45831da972fde.jpg",
            "aliases": ["gorra", "cap", "visera"]
        },
        {
            "name": "Chaqueta Jean",
            "price": 55.00,
            "category": "ropa",
            "image_url": "https://bambino.com.ve/wp-content/uploads/2024/09/077125001.jpg",
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
            "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ2ekAzoVVPBGg1bO01cVpYqjKJ2n2rOtsgjg&s",
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
