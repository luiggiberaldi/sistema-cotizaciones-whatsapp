from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ....domain.entities.product import Product
from ...database.product_repository import ProductRepository
from ...config.database import get_supabase_client
from ...security.auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])

def get_repository():
    return ProductRepository(get_supabase_client())

@router.get("/", response_model=List[Product], dependencies=[Depends(get_current_user)])
async def get_products(repo: ProductRepository = Depends(get_repository)):
    """
    Listar todos los productos (Protegido).
    """
    return repo.get_all()

@router.post("/", response_model=Product, dependencies=[Depends(get_current_user)])
async def create_product(product: Product, repo: ProductRepository = Depends(get_repository)):
    """
    Crear un nuevo producto (Protegido).
    """
    created = repo.create(product)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear el producto"
        )
    return created

@router.put("/{product_id}", response_model=Product, dependencies=[Depends(get_current_user)])
async def update_product(product_id: str, product: Product, repo: ProductRepository = Depends(get_repository)):
    """
    Actualizar un producto existente (Protegido).
    """
    updated = repo.update(product_id, product)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    return updated

@router.delete("/{product_id}", dependencies=[Depends(get_current_user)])
async def delete_product(product_id: str, repo: ProductRepository = Depends(get_repository)):
    """
    Eliminar un producto (Protegido).
    """
    success = repo.delete(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado"
        )
    return {"status": "success", "message": f"Producto {product_id} eliminado"}
