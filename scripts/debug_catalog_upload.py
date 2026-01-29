import asyncio
import os
import sys

# Agregar src al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.services.invoice_service import InvoiceService
from src.infrastructure.services.storage_service import StorageService
from src.domain.services.quote_service import QuoteService
from src.infrastructure.config.settings import settings

async def main():
    print("=== DIAGNÓSTICO DE ENVÍO DE CATÁLOGO ===")
    
    # 1. Verificar Servicio de Factura (PDF)
    try:
        invoice_service = InvoiceService()
        quote_service = QuoteService()
        products = quote_service.get_available_products()
        
        if products:
            pdf_path = invoice_service.generate_catalog_pdf(products)
            print(f"[OK] PDF generado en: {pdf_path}")
        else:
            print("[ERROR] No productos encontrados.")
            return

    except Exception as e:
        print(f"[ERROR] Generando PDF: {e}")
        return

    # 2. Verificar Servicio de Almacenamiento (Supabase)
    print(f"\n2. Subiendo a Supabase (Bucket: {settings.supabase_bucket_name})...")
    
    storage_service = StorageService()
    destination = "test_catalogs/test_catalog.pdf"
    
    # Intentar subir
    try:
        url = await storage_service.upload_pdf(pdf_path, destination)
        
        if url:
            # Eliminar trailing ? si existe
            if url.endswith('?'):
                url = url[:-1]
                
            print(f"[OK] SUBIDA EXITOSA.")
            print(f"URL Publica: {url}")
            
            # 3. Verificar Accesibilidad (Simular WhatsApp descargando)
            print(f"\n3. Verificando accesibilidad publica...")
            import httpx
            async with httpx.AsyncClient() as client:
                res = await client.get(url)
                if res.status_code == 200:
                    print(f"[OK] El archivo es accesible publicamente (Status 200).")
                    print(f"Content-Type: {res.headers.get('content-type')}")
                    print(f"Size: {len(res.content)} bytes")
                else:
                    print(f"[FAIL] El archivo NO es accesible (Status {res.status_code}).")
                    print("Posible causa: El bucket 'invoices' NO es publico en Supabase.")
        else:
            print("[FAIL] FALLO LA SUBIDA: La funcion retorno None.")
            
    except Exception as e:
        print(f"[ERROR] EXCEPCION: {e}")

if __name__ == "__main__":
    asyncio.run(main())
