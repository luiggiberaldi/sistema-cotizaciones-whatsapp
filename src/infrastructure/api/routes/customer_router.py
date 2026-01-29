from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
from ...database.customer_repository import CustomerRepository
from ...services.customer_service import CustomerService
from ...config.database import get_supabase_client

router = APIRouter(prefix="/customers", tags=["customers"])

def get_customer_service():
    client = get_supabase_client()
    repo = CustomerRepository(client)
    return CustomerService(repo)

@router.get("/", response_model=List[Dict])
async def get_customers(
    skip: int = 0, 
    limit: int = 100, 
    phone: Optional[str] = None,
    service: CustomerService = Depends(get_customer_service)
):
    """
    Obtener lista de clientes o buscar por teléfono.
    """
    if phone:
        customer = service.get_customer_by_phone(phone)
        return [customer] if customer else []
    
    return service.repository.get_all(skip, limit)

@router.put("/{customer_id}/address")
async def update_address(
    customer_id: str, 
    address_data: Dict,
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer address"""
    address = address_data.get('main_address')
    if not address:
        raise HTTPException(status_code=400, detail="Address required")
        
    updated = service.update_customer_address(customer_id, address)
    if not updated:
        raise HTTPException(status_code=404, detail="Customer not found")
    return updated
