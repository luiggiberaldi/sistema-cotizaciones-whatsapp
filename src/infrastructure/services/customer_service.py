from typing import Optional, Dict
from ..database.customer_repository import CustomerRepository

class CustomerService:
    """
    Servicio de dominio para la gestión de clientes (CRM).
    """
    
    def __init__(self, customer_repository: CustomerRepository):
        self.repository = customer_repository

    def get_or_create_customer(self, phone: str, name: str = None) -> Dict:
        """
        Obtiene un cliente existente o crea uno nuevo.
        Si existe y llega un nombre nuevo, actualiza el registro.
        """
        customer = self.repository.get_by_phone(phone)
        
        if customer:
            # Si tenemos nombre nuevo y el actual es genérico o diferente, actualizamos
            current_name = customer.get('full_name', '')
            if name and name != current_name:
                updated = self.repository.update_name(phone, name)
                if updated:
                    return updated
            return customer
        
        # Crear nuevo
        return self.repository.create(phone, name)

    def get_customer_by_phone(self, phone: str) -> Optional[Dict]:
        """Obtener cliente por teléfono."""
        return self.repository.get_by_phone(phone)

    def update_customer_address(self, customer_id: str, address: str) -> Optional[Dict]:
        """Actualizar dirección principal del cliente."""
        return self.repository.update(customer_id, {"main_address": address})

    def update_customer_dni(self, customer_id: str, dni: str) -> Optional[Dict]:
        """Actualizar DNI/RIF del cliente."""
        return self.repository.update(customer_id, {"dni_rif": dni})
