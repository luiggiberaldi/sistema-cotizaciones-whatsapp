"""
Endpoints REST para generar cotizaciones desde texto libre.
"""
from typing import List, Dict
from fastapi import APIRouter, HTTPException, status
from ....domain.services import QuoteService
from ....domain.entities.quote import Quote
from ..schemas import (
    GenerateQuoteFromTextRequest,
    GenerateQuoteFromTextResponse,
    QuoteResponseSchema,
    QuoteItemSchema,
    ProductSearchRequest
)


from ...database.product_repository import ProductRepository
from ...config.database import get_supabase_client
from fastapi.responses import FileResponse
from ...database.supabase_quote_repository import SupabaseQuoteRepository
from ....application.use_cases import GetQuoteUseCase
from ...services.invoice_service import InvoiceService

# Crear router
router = APIRouter(prefix="/generate", tags=["generate"])

# Inicializar repositorio y servicio
supabase = get_supabase_client()
product_repository = ProductRepository(supabase)
quote_service = QuoteService(product_repository)

# Servicios adicionales para generación de documentos
quote_repository = SupabaseQuoteRepository()
get_quote_use_case = GetQuoteUseCase(quote_repository)
invoice_service = InvoiceService()


def _entity_to_response(quote: Quote) -> QuoteResponseSchema:
    """Convertir entidad Quote a schema de respuesta."""
    items = [
        QuoteItemSchema(
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
            description=item.description
        )
        for item in quote.items
    ]
    
    return QuoteResponseSchema(
        id=quote.id,
        client_phone=quote.client_phone,
        items=items,
        total=quote.total,
        status=quote.status,
        notes=quote.notes,
        created_at=quote.created_at,
        updated_at=quote.updated_at
    )


@router.post(
    "/quote-from-text",
    response_model=GenerateQuoteFromTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar cotización desde texto libre",
    description="Genera una cotización parseando texto libre usando NLP ligero (ej: 'Quiero 2 zapatos y 1 camisa')"
)
async def generate_quote_from_text(request: GenerateQuoteFromTextRequest):
    """
    Generar cotización desde texto libre.
    
    Este endpoint usa NLP ligero (regex + fuzzy matching) para:
    1. Extraer productos y cantidades del texto
    2. Mapear productos a precios del catálogo
    3. Calcular totales con precisión decimal
    4. Generar cotización validada
    
    Ejemplos de texto válido:
    - "Quiero 2 zapatos y 1 camisa"
    - "necesito 3 camisas, 2 pantalones y 5 gorras"
    - "dame dos zapatos y una camisa"
    """
    try:
        # Generar cotización con detalles
        result = quote_service.generate_quote_with_details(
            text=request.text,
            client_phone=request.client_phone,
            fuzzy_threshold=request.fuzzy_threshold,
            status=request.status,
            notes=request.notes
        )
        
        quote = result['quote']
        confidence_scores = result['confidence_scores']
        
        return GenerateQuoteFromTextResponse(
            quote=_entity_to_response(quote),
            parsing_details=confidence_scores
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar cotización: {str(e)}"
        )


@router.get(
    "/products",
    response_model=List[Dict],
    summary="Listar productos disponibles",
    description="Obtiene la lista completa de productos del catálogo"
)
async def get_available_products():
    """Obtener lista de productos disponibles en el catálogo."""
    try:
        products = quote_service.get_available_products()
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener productos: {str(e)}"
        )


@router.post(
    "/search-product",
    response_model=Dict,
    summary="Buscar producto",
    description="Busca un producto en el catálogo usando fuzzy matching"
)
async def search_product(request: ProductSearchRequest):
    """
    Buscar un producto por nombre o alias.
    
    Usa fuzzy matching para encontrar productos similares.
    """
    try:
        product = quote_service.search_product(
            query=request.query,
            threshold=request.threshold
        )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró producto similar a '{request.query}'"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar producto: {str(e)}"
        )
