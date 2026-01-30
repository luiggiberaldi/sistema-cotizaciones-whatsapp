"""
Endpoints REST para Quote.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from ....domain.entities.quote import Quote, QuoteItem, QuoteStatus
from ....application.use_cases import (
    CreateQuoteUseCase,
    GetQuoteUseCase,
    ListQuotesUseCase,
    UpdateQuoteUseCase,
    DeleteQuoteUseCase,
    GetQuotesByPhoneUseCase
)
from ..schemas import (
    QuoteCreateSchema,
    QuoteUpdateSchema,
    QuoteResponseSchema,
    QuoteListResponseSchema,
    QuoteItemSchema
)
from ...database import SupabaseQuoteRepository
from ...security.auth import get_current_user
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/quotes", tags=["quotes"])

# Inicializar repositorio y casos de uso
repository = SupabaseQuoteRepository()
create_quote_use_case = CreateQuoteUseCase(repository)
get_quote_use_case = GetQuoteUseCase(repository)
list_quotes_use_case = ListQuotesUseCase(repository)
update_quote_use_case = UpdateQuoteUseCase(repository)
delete_quote_use_case = DeleteQuoteUseCase(repository)
get_quotes_by_phone_use_case = GetQuotesByPhoneUseCase(repository)

# Inicializar servicios adicionales
from ....infrastructure.services.invoice_service import InvoiceService
from fastapi.responses import FileResponse
invoice_service = InvoiceService()


def _schema_to_entity(schema: QuoteCreateSchema) -> Quote:
    """Convertir schema a entidad de dominio."""
    items = [
        QuoteItem(
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
            description=item.description
        )
        for item in schema.items
    ]
    
    return Quote(
        client_phone=schema.client_phone,
        items=items,
        total=schema.total,
        status=schema.status,
        notes=schema.notes
    )


def _entity_to_response(quote: Quote) -> QuoteResponseSchema:
    """Convertir entidad a schema de respuesta."""
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
    
    # Asegurar que status sea un Enum instance
    status_enum = quote.status
    print(f"DEBUG: Processing quote {quote.id}, status raw: {status_enum} (type: {type(status_enum)})")
    
    try:
        if isinstance(status_enum, str):
            status_enum = QuoteStatus(status_enum)
        print(f"DEBUG: Converted status: {status_enum} (type: {type(status_enum)})")
    except Exception as e:
        print(f"DEBUG: Failed to convert status: {e}")

    return QuoteResponseSchema(
        id=quote.id,
        client_phone=quote.client_phone,
        items=items,
        total=quote.total,
        status=status_enum,
        notes=quote.notes,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        client_name=quote.client_name,
        client_dni=quote.client_dni,
        client_address=quote.client_address
    )


@router.post(
    "/",
    response_model=QuoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cotización",
    description="Crea una nueva cotización con validación estricta de datos"
)
async def create_quote(
    quote_data: QuoteCreateSchema,
    current_user: dict = Depends(get_current_user)
):
    """Crear una nueva cotización."""
    try:
        quote = _schema_to_entity(quote_data)
        created_quote = await create_quote_use_case.execute(quote)
        return _entity_to_response(created_quote)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la cotización: {str(e)}"
        )


@router.get(
    "/{quote_id}",
    response_model=QuoteResponseSchema,
    summary="Obtener cotización",
    description="Obtiene una cotización por su ID"
)
async def get_quote(quote_id: int):
    """Obtener una cotización por ID."""
    quote = await get_quote_use_case.execute(quote_id)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización con ID {quote_id} no encontrada"
        )
    
    return _entity_to_response(quote)


@router.get(
    "/",
    response_model=QuoteListResponseSchema,
    summary="Listar cotizaciones",
    description="Lista todas las cotizaciones con paginación y filtros opcionales"
)
async def list_quotes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    quote_status: Optional[str] = Query(None, alias="status", description="Filtrar por estado"),
    current_user: dict = Depends(get_current_user)
):
    """Listar cotizaciones con paginación."""
    try:
        quotes = await list_quotes_use_case.execute(skip, limit, quote_status)
        
        return QuoteListResponseSchema(
            quotes=[_entity_to_response(quote) for quote in quotes],
            total=len(quotes),
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error en list_quotes: {e}", exc_info=True)
        # Debugging: write to file
        with open("last_error.log", "w") as f:
            f.write(f"Error: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{quote_id}",
    response_model=QuoteResponseSchema,
    summary="Actualizar cotización",
    description="Actualiza una cotización existente"
)
async def update_quote(quote_id: int, quote_data: QuoteCreateSchema):
    """Actualizar una cotización."""
    try:
        quote = _schema_to_entity(quote_data)
        updated_quote = await update_quote_use_case.execute(quote_id, quote)
        
        if not updated_quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quote_id} no encontrada"
            )
        
        return _entity_to_response(updated_quote)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la cotización: {str(e)}"
        )


@router.delete(
    "/{quote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cotización",
    description="Elimina una cotización por su ID"
)
async def delete_quote(quote_id: int):
    """Eliminar una cotización."""
    deleted = await delete_quote_use_case.execute(quote_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización con ID {quote_id} no encontrada"
        )
    
    return None


@router.post(
    "/{quote_id}/generate-pdf",
    summary="Generar PDF de Cotización",
    description="Genera y devuelve el archivo PDF de la cotización."
)
async def generate_quote_pdf(quote_id: int):
    """Generar y descargar PDF de la cotización."""
    try:
        quote = await get_quote_use_case.execute(quote_id)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quote_id} no encontrada"
            )
            
        # Preparar datos para el servicio de facturas
        # Convertimos la entidad a dict para el servicio
        quote_data = {
            'id': quote.id,
            'client_phone': quote.client_phone,
            'client_name': quote.client_name,
            'client_dni': quote.client_dni,
            'client_address': quote.client_address,
            'total': quote.total,
            'items': [
                {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'subtotal': item.subtotal
                }
                for item in quote.items
            ]
        }
        
        pdf_path = invoice_service.generate_invoice_pdf(quote_data)
        
        return FileResponse(
            path=pdf_path,
            filename=f"Cotizacion_{quote.id}.pdf",
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Error generando PDF: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get(
    "/phone/{client_phone}",
    response_model=List[QuoteResponseSchema],
    summary="Obtener cotizaciones por teléfono",
    description="Obtiene todas las cotizaciones de un cliente por su número de teléfono"
)
async def get_quotes_by_phone(client_phone: str):
    """Obtener cotizaciones por teléfono del cliente."""
    quotes = await get_quotes_by_phone_use_case.execute(client_phone)
    
    return [_entity_to_response(quote) for quote in quotes]
