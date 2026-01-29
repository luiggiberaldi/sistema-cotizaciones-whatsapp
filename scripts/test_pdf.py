import sys
import io

# Force UTF-8 stdout for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os

# PYTHONPATH fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.services.invoice_service import InvoiceService

def test_pdf():
    print("--- Test de Generación de PDF ---")
    service = InvoiceService(output_dir="test_outputs")
    
    quote_data = {
        "id": "12345",
        "client_phone": "+584121234567",
        "total": 150.50,
        "items": [
            {"product_name": "Zapato Deportivo", "quantity": 2, "unit_price": 50.0, "subtotal": 100.0},
            {"product_name": "Camisa Polo", "quantity": 1, "unit_price": 50.5, "subtotal": 50.5}
        ]
    }
    
    try:
        path = service.generate_invoice_pdf(quote_data)
        print(f"✅ PDF generado exitosamente en: {path}")
        
        # Verificar que el archivo existe
        if os.path.exists(path):
            print(f"📏 Tamaño del archivo: {os.path.getsize(path)} bytes")
        else:
            print("❌ El archivo no se encontró.")
            
    except Exception as e:
        print(f"❌ Error durante la generación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf()
