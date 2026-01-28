import sys
import io

# Force UTF-8 stdout for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
import os
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar env
load_dotenv()

# Imports del proyecto
from src.infrastructure.config.database import get_supabase_client
from src.infrastructure.database.product_repository import ProductRepository
from src.infrastructure.database.session_repository import SessionRepository
from src.domain.repositories.quote_repository import QuoteRepository # Abstract
# Necesitamos una implementación concreta de QuoteRepo o un Mock
class MockQuoteRepository(QuoteRepository):
    async def create(self, quote):
        print(f"[MOCK DB] Guardando cotización: {quote}")
        quote.id = "mock-id-123"
        return quote
    async def get_by_id(self, id): return None
    async def get_all(self, **kwargs): return []
    async def update(self, id, quote): return None
    async def delete(self, id): return True
    async def get_by_phone(self, phone): return []

from src.domain.services.quote_service import QuoteService
from src.infrastructure.external.whatsapp_service import WhatsAppService
from src.infrastructure.external.retry_queue import RetryQueue
from src.application.use_cases.whatsapp_use_cases import ProcessWhatsAppMessageUseCase

# Mock WhatsApp Service para no enviar mensajes reales pero ver el log
class MockWhatsAppService(WhatsAppService):
    async def send_message(self, to, message):
        print(f"\n[MOCK WHATSAPP] Enviando a {to}:\n{message}\n")
        return {"status": "mock_sent"}
    
    async def send_quote_message(self, to, quote_data):
        print(f"\n[MOCK WHATSAPP] Enviando Cotización a {to}: {quote_data}\n")
        return {"status": "mock_sent"}
        
    async def mark_message_as_read(self, message_id):
        print(f"[MOCK WHATSAPP] Mensaje {message_id} marcado como leído.")

async def main():
    print("=== Iniciando Debug Flow ===")
    
    try:
        # 1. Inicializar dependencias reales (Supabase)
        print("1. Conectando a Supabase...")
        supabase = get_supabase_client()
        
        # 2. Repositorios
        print("2. Inicializando Repositorios...")
        product_repo = ProductRepository(supabase)
        session_repo = SessionRepository(supabase)
        quote_repo = MockQuoteRepository() # Usamos mock para cotizaciones por ahora
        
        # 3. Servicios
        print("3. Inicializando Servicios...")
        quote_service = QuoteService(product_repo)
        
        # Verificar carga de productos
        print(f"   -> Productos en caché: {len(quote_service.product_cache)}")
        if quote_service.product_cache:
            print(f"   -> Ejemplo: {quote_service.product_cache[0]['name']}")
        else:
            print("   -> ⚠️ CACHÉ VACÍO")

        whatsapp_service = MockWhatsAppService()
        retry_queue = RetryQueue()
        
        # 4. Caso de Uso
        use_case = ProcessWhatsAppMessageUseCase(
            quote_service=quote_service,
            quote_repository=quote_repo,
            whatsapp_service=whatsapp_service,
            retry_queue=retry_queue,
            session_repository=session_repo
        )
        
        # 5. Pruebas
        print("\n=== PRUEBA 1: Saludo ===")
        await use_case.execute({
            'from': '584121234567',
            'text': 'Hola',
            'message_id': 'msg_1'
        })
        
        print("\n=== PRUEBA 2: Consulta de Precio (Intención) ===")
        await use_case.execute({
            'from': '584121234567',
            'text': 'Precio de la camisa',
            'message_id': 'msg_2'
        })
        
        print("\n=== PRUEBA 3: Pedido (Parsing) ===")
        await use_case.execute({
            'from': '584121234567',
            'text': 'Quiero 2 zapatos',
            'message_id': 'msg_3'
        })

    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
