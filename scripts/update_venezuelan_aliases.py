import asyncio
import os
import sys

# Añadir directorio raíz al path para importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.config.settings import settings
from supabase import create_client

async def update_aliases():
    print("Conectando a Supabase...")
    supabase = create_client(settings.supabase_url, settings.supabase_service_key) # Usar service key si es posible para asegurar permisos, sino anon key
    
    # Mapeo de Productos -> Alias Venezolanos
    alias_map = {
        'zapato': ['zapato', 'zapatos', 'calzado', 'tenis', 'gomas', 'zapatillas', 'corte bajo', 'kicks'],
        'camisa': ['camisa', 'franela', 'chemise', 'polera', 'top', 'blusa', 'remera'],
        'pantalon': ['pantalon', 'pantalón', 'jean', 'bluejean', 'mono', 'short', 'bermuda'],
        'gorra': ['gorra', 'cachucha', 'vicera'],
        'chaqueta': ['chaqueta', 'sueter', 'abrigo', 'hoodie', 'chamarra'],
        'bolso': ['bolso', 'morral', 'cartera', 'koala', 'bandolero'],
        'media': ['medias', 'calcetines'] # Singular 'media' para matching
    }

    print("Iniciando actualización de alias...")

    for key, aliases in alias_map.items():
        # Buscar productos que contengan la palabra clave (ej: "Zapato Deportivo" coincide con "zapato")
        # Usamos ilike para case-insensitive search
        try:
            print(f"Buscando productos tipo '{key}'...")
            response = supabase.table('products').select("*").ilike('name', f'%{key}%').execute()
            products = response.data
            
            if not products:
                print(f"  - No se encontraron productos para '{key}'")
                continue

            for product in products:
                print(f"  - Actualizando: {product['name']}...")
                
                # Update
                update_resp = supabase.table('products').update({
                    'aliases': aliases
                }).eq('id', product['id']).execute()
                
                if update_resp.data:
                    print(f"    ✓ Alias actualizados: {aliases}")
                else:
                    print(f"    ✗ Error actualizando {product['name']}")
                    
        except Exception as e:
            print(f"Error procesando '{key}': {e}")

    print("\n¡Actualización completada!")

if __name__ == "__main__":
    asyncio.run(update_aliases())
