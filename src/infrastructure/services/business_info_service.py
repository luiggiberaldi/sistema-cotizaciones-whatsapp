import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..database.business_info_repository import BusinessInfoRepository
from ...domain.entities.business_info import BusinessInfo

logger = logging.getLogger(__name__)

class BusinessInfoService:
    _cache: Dict[str, str] = {}
    _last_update: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(minutes=10)

    def __init__(self, repository: Optional[BusinessInfoRepository] = None):
        self.repository = repository or BusinessInfoRepository()

    def _should_refresh_cache(self) -> bool:
        if not self._last_update:
            return True
        return datetime.now() - self._last_update > self._cache_ttl

    def _refresh_cache(self):
        """Recargar caché desde BD."""
        try:
            items = self.repository.get_all()
            self._cache = {item.key: item.value for item in items}
            self._last_update = datetime.now()
            logger.info("Caché de Business Info actualizado")
        except Exception as e:
            logger.error(f"Error actualizando caché de Business Info: {e}")

    def get_value(self, key: str, default: str = "") -> str:
        """Obtener valor por clave (leído de caché)."""
        if self._should_refresh_cache() or key not in self._cache:
            self._refresh_cache()
        return self._cache.get(key, default)

    def get_all_info(self) -> List[BusinessInfo]:
        """Obtener toda la info (directo de BD para dashboard)."""
        return self.repository.get_all()

    def update_info(self, updates: List[Dict]) -> List[BusinessInfo]:
        """Actualizar información y limpiar caché."""
        updated = self.repository.update_bulk(updates)
        # Invalidar caché forzando recarga próxima vez
        self._last_update = None
        return updated
