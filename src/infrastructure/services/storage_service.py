import logging
from typing import Optional
from supabase import Client
from ..config.database import get_supabase_client
from ..config.settings import settings

logger = logging.getLogger(__name__)

class StorageService:
    """
    Servicio para interactuar con Supabase Storage.
    """
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client or get_supabase_client()
        self.bucket_name = settings.supabase_bucket_name

    async def upload_pdf(self, file_path: str, destination_path: str) -> Optional[str]:
        """
        Sube un archivo PDF al bucket de Supabase.
        
        Args:
            file_path: Ruta local del archivo.
            destination_path: Ruta en el bucket (ej: "invoices/quote_123.pdf").
            
        Returns:
            URL pública del archivo o None si falla.
        """
        try:
            with open(file_path, 'rb') as f:
                self.supabase.storage.from_(self.bucket_name).upload(
                    path=destination_path,
                    file=f,
                    file_options={"content-type": "application/pdf"}
                )
            
            # Obtener URL pública
            res = self.supabase.storage.from_(self.bucket_name).get_public_url(destination_path)
            return res
            
        except Exception as e:
            logger.error(f"Error subiendo archivo a Supabase Storage: {e}")
            return None
