"""
Servicio de dominio para generar cotizaciones desde texto libre.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from ..entities.quote import Quote, QuoteItem, QuoteStatus
from .text_parser import TextParser


class QuoteService:
    """
    Servicio para generar cotizaciones desde texto libre.
    
    Responsabilidades:
    - Cargar catálogo de productos
    - Parsear texto libre
    - Generar cotización con cálculos exactos
    - Validar datos
    """
    
    def __init__(self, product_repository: Optional['ProductRepository'] = None):
        """
        Inicializar servicio.
        
        Args:
            product_repository: Repositorio de productos (opcional para pruebas)
        """
        self.product_repository = product_repository
        self.product_cache = []
        self.last_cache_update = None
        self.cache_duration = timedelta(minutes=10)
        
        # Cargar catálogo inicial
        self._load_catalog()
        
        # Inicializar parser con el catálogo cargado
        self.parser = TextParser(self.product_cache)
    
    def _load_catalog(self) -> List[Dict]:
        """
        Cargar catálogo de productos con caché.
        
        Returns:
            Lista de productos
        """
        now = datetime.now()
        
        # Si hay caché válido Y NO ESTÁ VACÍO, retornarlo
        if (self.product_cache and 
            self.last_cache_update and 
            now - self.last_cache_update < self.cache_duration):
            return self.product_cache
            
        # Si no hay repositorio, intentar cargar mock (para tests legacy)
        if not self.product_repository:
            # Fallback a archivo JSON si no hay repositorio (legacy support)
            base_dir = Path(__file__).parent.parent.parent.parent
            catalog_path = base_dir / "data" / "products_catalog.json"
            if catalog_path.exists():
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.product_cache = data.get('products', [])
                    self.last_cache_update = now
                    return self.product_cache
            return []
            
        # Cargar de repositorio
        try:
            products = self.product_repository.get_all_products()
            if products:
                self.product_cache = products
                self.last_cache_update = now
                
                # Actualizar parser si ya existe
                if hasattr(self, 'parser'):
                    self.parser.update_catalog(self.product_cache)
            else:
                print("Warning: Repositorio retornó lista vacía de productos")
                
        except Exception as e:
            # Log error y retornar caché anterior si existe
            print(f"Error actualizando caché de productos: {e}")
            
        return self.product_cache
    
    def _calculate_precise_decimal(self, value: float) -> Decimal:
        """
        Calcular valor decimal preciso para evitar errores de punto flotante.
        
        Args:
            value: Valor float
            
        Returns:
            Decimal con 2 decimales
        """
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _create_quote_item(self, product: Dict, quantity: int) -> QuoteItem:
        """
        Crear un QuoteItem desde un producto y cantidad.
        
        Args:
            product: Diccionario del producto
            quantity: Cantidad
            
        Returns:
            QuoteItem con cálculos exactos
        """
        # Usar Decimal para cálculos precisos
        unit_price_decimal = self._calculate_precise_decimal(product['price'])
        quantity_decimal = Decimal(str(quantity))
        subtotal_decimal = unit_price_decimal * quantity_decimal
        
        # Convertir a float para Pydantic
        unit_price = float(unit_price_decimal)
        subtotal = float(subtotal_decimal)
        
        return QuoteItem(
            product_name=product['name'],
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            description=f"Categoría: {product.get('category', 'N/A')}"
        )
    
    def generate_quote_from_text(
        self,
        text: str,
        client_phone: str,
        fuzzy_threshold: int = 70,
        status: QuoteStatus = QuoteStatus.DRAFT,
        notes: Optional[str] = None
    ) -> Quote:
        """
        Generar cotización desde texto libre.
        
        Args:
            text: Texto libre (ej: "Quiero 2 zapatos y 1 camisa")
            client_phone: Teléfono del cliente
            fuzzy_threshold: Umbral para fuzzy matching (0-100)
            status: Estado inicial de la cotización
            notes: Notas adicionales
            
        Returns:
            Quote generada con cálculos exactos
            
        Raises:
            ValueError: Si no se pueden extraer productos del texto
            
        Example:
            >>> service = QuoteService()
            >>> quote = service.generate_quote_from_text(
            ...     "Quiero 2 zapatos y 1 camisa",
            ...     "+58 412-1234567"
            ... )
            >>> print(quote.total)
            117.48
        """
        # Parsear texto
        parsed_items = self.parser.parse(text, fuzzy_threshold)
        
        if not parsed_items:
            raise ValueError(
                f"No se pudieron extraer productos del texto: '{text}'. "
                "Intenta ser más específico (ej: '2 zapatos y 1 camisa')"
            )
        
        # Crear items de cotización
        quote_items = []
        for item in parsed_items:
            quote_item = self._create_quote_item(
                item['product'],
                item['quantity']
            )
            quote_items.append(quote_item)
        
        # Calcular total con precisión decimal
        total_decimal = Decimal('0')
        for item in quote_items:
            total_decimal += self._calculate_precise_decimal(item.subtotal)
        
        total = float(total_decimal)
        
        # Crear cotización
        quote = Quote(
            client_phone=client_phone,
            items=quote_items,
            total=total,
            status=status,
            notes=notes
        )
        
        return quote
    
    def generate_quote_with_details(
        self,
        text: str,
        client_phone: str,
        fuzzy_threshold: int = 70,
        status: QuoteStatus = QuoteStatus.DRAFT,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Generar cotización con detalles de parsing.
        
        Returns:
            Diccionario con 'quote', 'parsed_items', 'confidence_scores'
        """
        # Parsear con confianza
        parsed_items = self.parser.parse_with_confidence(text, fuzzy_threshold)
        
        if not parsed_items:
            raise ValueError(
                f"No se pudieron extraer productos del texto: '{text}'"
            )
        
        # Crear items de cotización
        quote_items = []
        confidence_scores = []
        
        for item in parsed_items:
            quote_item = self._create_quote_item(
                item['product'],
                item['quantity']
            )
            quote_items.append(quote_item)
            
            confidence_scores.append({
                'product': item['product']['name'],
                'matched_text': item['matched_text'],
                'matched_to': item['matched_to'],
                'confidence': item['confidence']
            })
        
        # Calcular total
        total_decimal = Decimal('0')
        for item in quote_items:
            total_decimal += self._calculate_precise_decimal(item.subtotal)
        
        total = float(total_decimal)
        
        # Crear cotización
        quote = Quote(
            client_phone=client_phone,
            items=quote_items,
            total=total,
            status=status,
            notes=notes
        )
        
        return {
            'quote': quote,
            'parsed_items': parsed_items,
            'confidence_scores': confidence_scores
        }
    
    def get_available_products(self) -> List[Dict]:
        """
        Obtener lista de productos disponibles.
        
        Returns:
            Lista de productos del catálogo
        """
        return self.product_cache
    
    def search_product(self, query: str, threshold: int = 70) -> Optional[Dict]:
        """
        Buscar un producto por nombre o alias.
        
        Args:
            query: Texto a buscar
            threshold: Umbral de similitud
            
        Returns:
            Producto encontrado o None
        """
        parsed = self.parser.parse(f"1 {query}", threshold)
        
        if parsed:
            return parsed[0]['product']
        
        return None
