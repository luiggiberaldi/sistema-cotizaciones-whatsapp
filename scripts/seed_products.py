import json
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")
    exit(1)

# Usar service key si existe para saltar RLS, sino usar key normal
target_key = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
supabase = create_client(SUPABASE_URL, target_key)

def seed_products():
    """Migrar productos de JSON a Supabase."""
    base_dir = Path(__file__).parent.parent
    json_path = base_dir / "data" / "products_catalog.json"
    
    if not json_path.exists():
        print(f"No se encontró archivo JSON en {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        products = data.get('products', [])
    
    print(f"Encontrados {len(products)} productos en JSON.")
    
    success_count = 0
    for p in products:
        try:
            # Preparar objeto para inserción
            product_data = {
                "name": p["name"],
                "price": p["price"],
                "aliases": p.get("aliases", []),
                "category": p.get("category", "General"),
                "stock": 100 # Default stock
            }
            
            # Insertar en Supabase
            supabase.table("products").insert(product_data).execute()
            print(f"Insertado: {p['name']}")
            success_count += 1
        except Exception as e:
            print(f"Error insertando {p['name']}: {e}")
            
    print(f"\nMigración completada. {success_count}/{len(products)} productos insertados.")

if __name__ == "__main__":
    seed_products()
