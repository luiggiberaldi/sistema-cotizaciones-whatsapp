import asyncio
import os
import sys
from datetime import datetime

# Agregar src al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.database.supabase_quote_repository import SupabaseQuoteRepository
from src.domain.entities.quote import Quote, QuoteItem, QuoteStatus

async def main():
    print("=== DIAGNÓSTICO DE ESQUEMA DE BASE DE DATOS ===")
    
    repo = SupabaseQuoteRepository()
    
    # Crear una cotización de prueba con los nuevos campos
    test_quote = Quote(
        client_phone="580000000000",
        items=[QuoteItem(product_name="Test Product", quantity=1, unit_price=1.0, subtotal=1.0)],
        total=1.0,
        status=QuoteStatus.DRAFT,
        created_at=datetime.utcnow(),
        client_name="Test User",      # CAMPO NUEVO
        client_dni="123456",          # CAMPO NUEVO
        client_address="Test Addr",   # CAMPO NUEVO
        notes="Test de migración"
    )
    
    print("\nIntentando insertar cotización con campos nuevos (client_name, dni, address)...")
    
    try:
        created = await repo.create(test_quote)
        print(f"✅ ÉXITO: La base de datos aceptó los nuevos campos. ID: {created.id}")
        
        # Limpiar
        await repo.delete(created.id)
        print("✅ Limpieza completada (cotización de prueba eliminada).")
        
    except Exception as e:
        print("\n❌ FALLÓ LA INSERCIÓN.")
        print("-" * 50)
        print(f"Error detallado: {e}")
        print("-" * 50)
        
        error_msg = str(e).lower()
        if "column" in error_msg and "does not exist" in error_msg:
             print("\n⚠️ DIAGNÓSTICO: Faltan las columnas en la tabla 'quotes'.")
             print("SOLUCIÓN: Debes ejecutar el script 'migrations/007_add_client_data_columns.sql' en Supabase.")
        else:
             print("\n⚠️ DIAGNÓSTICO: Error desconocido. Revisa el mensaje arriba.")

if __name__ == "__main__":
    asyncio.run(main())
