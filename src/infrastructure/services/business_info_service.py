import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..database.business_info_repository import BusinessInfoRepository
from ...domain.entities.business_info import BusinessInfo

logger = logging.getLogger(__name__)

class BusinessInfoService:
    _cache: Dict[str, str] = {}
    _last_update: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(seconds=30)

    def __init__(self, repository: Optional[BusinessInfoRepository] = None):
        self.repository = repository or BusinessInfoRepository()

    def _should_refresh_cache(self) -> bool:
        if not BusinessInfoService._last_update:
            return True
        return datetime.now() - BusinessInfoService._last_update > self._cache_ttl

    def _refresh_cache(self):
        """Recargar caché desde BD."""
        try:
            items = self.repository.get_all()
            # Actualizar atributo de CLASE para compartir entre instancias
            BusinessInfoService._cache = {item.key: item.value for item in items}
            BusinessInfoService._last_update = datetime.now()
            logger.info("Caché de Business Info actualizado")
        except Exception as e:
            logger.error(f"Error actualizando caché de Business Info: {e}")

    def get_value(self, key: str, default: str = "") -> str:
        """Obtener valor por clave (leído de caché)."""
        if self._should_refresh_cache() or key not in BusinessInfoService._cache:
            self._refresh_cache()
        return BusinessInfoService._cache.get(key, default)

    def get_all_info(self) -> List[BusinessInfo]:
        """Obtener toda la info (directo de BD para dashboard)."""
        return self.repository.get_all()

    def get_info_by_key(self, key: str) -> Optional[BusinessInfo]:
        """Busca un objeto BusinessInfo específico por su clave."""
        # Aseguramos que la info esté cargada (usando el método existente que tiene caché)
        all_info = self.get_all_info()
        
        # Buscamos la clave en la lista
        for item in all_info:
            if item.key == key:
                return item
        return None

    def update_info(self, updates: List[Dict]) -> List[BusinessInfo]:
        """Actualizar información y limpiar caché."""
        updated = self.repository.update_bulk(updates)
        # Invalidar caché forzando recarga próxima vez (en TODAS las instancias)
        BusinessInfoService._last_update = None
        return updated
