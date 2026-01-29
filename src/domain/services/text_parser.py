"""
Parser de texto para extraer productos y cantidades.
Usa NLP ligero con regex y fuzzy matching.
"""
import re
from typing import List, Dict, Tuple, Optional
from thefuzz import fuzz, process


class TextParser:
    """
    Parser de texto libre para extraer productos y cantidades.
    
    Ejemplos:
    - "Quiero 2 zapatos y 1 camisa"
    - "necesito 3 camisas, 2 pantalones y 1 chaqueta"
    - "dame 5 gorras"
    """
    
    # Patrones de números en español
    NUMERO_PALABRAS = {
        'un': 1, 'una': 1, 'uno': 1,
        'unos': 1, 'unas': 1, 'el': 1, 'la': 1, 'los': 1, 'las': 1, # Artículos como cantidad 1
        'dos': 2,
        'tres': 3,
        'cuatro': 4,
        'cinco': 5,
        'seis': 6,
        'siete': 7,
        'ocho': 8,
        'nueve': 9,
        'diez': 10,
        'once': 11,
        'doce': 12,
        'trece': 13,
        'catorce': 14,
        'quince': 15,
        'veinte': 20,
        'treinta': 30,
        'cuarenta': 40,
        'cincuenta': 50,
    }
    
    # Palabras a ignorar
    STOPWORDS = {
        'quiero', 'necesito', 'dame', 'por', 'favor', 'me', 'gustaria',
        'quisiera', 'deseo', 'comprar', 'y', 'de', 'para', 'con', 'sin',
        'precio', 'costo', 'valor', 'cuanto', 'como', 'donde' # Nuevas stopwords de ruido
    }
    
    def __init__(self, product_catalog: List[Dict]):
        """
        Inicializar parser con catálogo de productos.
        
        Args:
            product_catalog: Lista de productos con 'name' y 'aliases'
        """
        self.product_catalog = product_catalog
        self._build_product_index()
    
    def _build_product_index(self):
        """Construir índice de productos con todos sus aliases."""
        self.product_index = {}
        
        for product in self.product_catalog:
            # Agregar nombre principal
            name_lower = product['name'].lower()
            self.product_index[name_lower] = product
            
            # Agregar aliases
            for alias in product.get('aliases', []):
                alias_lower = alias.lower()
                self.product_index[alias_lower] = product

    def update_catalog(self, new_catalog: List[Dict]):
        """Actualizar el catálogo y reconstruir el índice."""
        self.product_catalog = new_catalog
        self._build_product_index()
    
    def _normalize_text(self, text: str) -> str:
        """Normalizar texto: minúsculas y sin acentos."""
        text = text.lower()
        
        # Remover acentos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _extract_quantity_product_pairs(self, text: str) -> List[Tuple[int, str]]:
        """
        Extraer pares de (cantidad, producto) del texto.
        
        Patrones soportados:
        - "2 zapatos"
        - "zapatos" (cantidad = 1 por defecto)
        - "unos zapatos"
        """
        text = self._normalize_text(text)
        
        # Palabras de relleno/unidades a ignorar entre el número y el producto
        fillers = r'(?:(?:pares|unidades|piezas|cajas|paquetes|botellas|kilos|gramos|litros|de)\s+)*'
        
        # Ordenar claves por longitud para regex (primero las más largas)
        num_keys = sorted(self.NUMERO_PALABRAS.keys(), key=len, reverse=True)
        num_pattern = '|'.join(map(re.escape, num_keys))
        
        # Patrón: (opcional: número + espacio) + relleno + producto
        # Group 1: Cantidad (opcional)
        # Group 2: Producto (obligatorio, al menos 2 letras)
        pattern = r'(?:(\d+|' + num_pattern + r')\s+)?' + fillers + r'([a-zñ]{2,})'
        
        pairs = []
        matches = re.finditer(pattern, text)
        
        for match in matches:
            quantity_str = match.group(1)
            product_str = match.group(2)
            
            # Ignorar si es stopword
            if product_str in self.STOPWORDS:
                continue
            
            # Determinar cantidad
            quantity = 1
            if quantity_str:
                if quantity_str.isdigit():
                    quantity = int(quantity_str)
                else:
                    quantity = self.NUMERO_PALABRAS.get(quantity_str, 1)
            
            pairs.append((quantity, product_str))
        
        return pairs
    
    def _find_best_product_match(self, product_text: str, threshold: int = 70) -> Optional[Dict]:
        """
        Encontrar el mejor match de producto usando fuzzy matching.
        
        Args:
            product_text: Texto del producto a buscar
            threshold: Umbral mínimo de similitud (0-100)
            
        Returns:
            Producto encontrado o None
        """
        # Primero intentar match exacto
        if product_text in self.product_index:
            return self.product_index[product_text]
        
        # Fuzzy matching contra todos los nombres y aliases
        all_names = list(self.product_index.keys())
        
        # Obtener el mejor match
        best_match = process.extractOne(
            product_text,
            all_names,
            scorer=fuzz.ratio
        )
        
        if best_match and best_match[1] >= threshold:
            matched_name = best_match[0]
            return self.product_index[matched_name]
        
        return None
    
    def parse(self, text: str, fuzzy_threshold: int = 70) -> List[Dict]:
        """
        Parsear texto libre y extraer productos con cantidades.
        
        Args:
            text: Texto libre (ej: "Quiero 2 zapatos y 1 camisa")
            fuzzy_threshold: Umbral para fuzzy matching (0-100)
            
        Returns:
            Lista de diccionarios con 'product', 'quantity'
            
        Example:
            >>> parser.parse("Quiero 2 zapatos y 1 camisa")
            [
                {'product': {...}, 'quantity': 2},
                {'product': {...}, 'quantity': 1}
            ]
        """
        # Extraer pares (cantidad, producto)
        pairs = self._extract_quantity_product_pairs(text)
        
        results = []
        for quantity, product_text in pairs:
            # Buscar producto en catálogo
            product = self._find_best_product_match(product_text, fuzzy_threshold)
            
            if product:
                results.append({
                    'product': product,
                    'quantity': quantity
                })
        
        return results
    
    def parse_with_confidence(self, text: str, fuzzy_threshold: int = 70) -> List[Dict]:
        """
        Parsear texto y retornar resultados con score de confianza.
        
        Returns:
            Lista de diccionarios con 'product', 'quantity', 'confidence', 'matched_text'
        """
        text_normalized = self._normalize_text(text)
        pairs = self._extract_quantity_product_pairs(text)
        
        results = []
        for quantity, product_text in pairs:
            # Obtener todos los matches con scores
            all_names = list(self.product_index.keys())
            matches = process.extract(
                product_text,
                all_names,
                scorer=fuzz.ratio,
                limit=1
            )
            
            if matches and matches[0][1] >= fuzzy_threshold:
                matched_name = matches[0][0]
                confidence = matches[0][1]
                product = self.product_index[matched_name]
                
                results.append({
                    'product': product,
                    'quantity': quantity,
                    'confidence': confidence,
                    'matched_text': product_text,
                    'matched_to': matched_name
                })
        
        return results
