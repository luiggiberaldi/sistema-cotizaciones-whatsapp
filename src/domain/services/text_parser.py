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
    Usa estrategia de "Longest Match First" para evitar duplicados en nombres compuestos.
    """
    
    # Patrones de números en español (Mantenemos igual)
    NUMERO_PALABRAS = {
        'un': 1, 'una': 1, 'uno': 1,
        'unos': 1, 'unas': 1, 'el': 1, 'la': 1, 'los': 1, 'las': 1,
        'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
        'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
        'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
        'veinte': 20, 'treinta': 30, 'cuarenta': 40, 'cincuenta': 50,
    }
    
    STOPWORDS = {
        'quiero', 'necesito', 'dame', 'por', 'favor', 'me', 'gustaria',
        'quisiera', 'deseo', 'comprar', 'y', 'de', 'para', 'con', 'sin',
        'precio', 'costo', 'valor', 'cuanto', 'como', 'donde'
    }
    
    def __init__(self, product_catalog: List[Dict]):
        self.product_catalog = product_catalog
        self._build_match_list()
    
    def _normalize_text(self, text: str) -> str:
        """Normalizar texto: minúsculas y sin acentos."""
        text = text.lower()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def _build_match_list(self):
        """
        Construir lista de (alias_normalizado, producto) ordenada por longitud.
        """
        self.match_list = [] # List of tuples: (normalized_alias, product_dict)
        
        for product in self.product_catalog:
            # Incluir nombre principal
            norm_name = self._normalize_text(product['name'])
            self.match_list.append((norm_name, product))
            
            # Incluir aliases
            for alias in product.get('aliases', []):
                norm_alias = self._normalize_text(alias)
                self.match_list.append((norm_alias, product))
        
        # Ordenar por longitud descendente para priorizar "Chaqueta Jean" sobre "Jean"
        self.match_list.sort(key=lambda x: len(x[0]), reverse=True)

    def update_catalog(self, new_catalog: List[Dict]):
        self.product_catalog = new_catalog
        self._build_match_list()
    
    def _extract_quantity_for_match(self, text: str, start_index: int, end_index: int) -> int:
        """
        Buscar cantidad numérica o textual ANTES del match.
        """
        # Mirar texto anterior al match (hasta 30 caracteres atrás)
        lookbehind_limit = max(0, start_index - 30)
        preceding_text = text[lookbehind_limit:start_index]
        
        # Tokenizar palabras previas (reversa)
        words = re.split(r'\s+', preceding_text.strip())
        if not words:
            return 1
            
        # Buscar el último número/palabra numérica encontrada
        for word in reversed(words):
            if not word: continue
            
            # Chequear dígitos
            if word.isdigit():
                return int(word)
            
            # Chequear palabras numéricas
            norm_word = self._normalize_text(word)
            if norm_word in self.NUMERO_PALABRAS:
                return self.NUMERO_PALABRAS[norm_word]
                
            # Si encontramos una stopword o filler, seguimos buscando
            # Si encontramos algo que parece otro producto o palabra clave fuerte, paramos
            # Por simplicidad, asumimos 1 si no encontramos numero inmediato
            
        return 1

    def parse(self, text: str, fuzzy_threshold: int = 70) -> List[Dict]:
        """
        Parsear usando eliminación de ocurrencias encontradas.
        """
        text_norm = self._normalize_text(text)
        results = []
        
        # Iterar sobre aliases ordenados por longitud
        for alias, product in self.match_list:
            # Usamos regex con word boundaries para evitar matches parciales (ej: "ala" en "pala")
            # Escapeamos alias para seguridad regex
            pattern = r'\b' + re.escape(alias) + r'\b'
            
            # Buscar TODAS las ocurrencias de este alias
            # Lo hacemos en bucle porque re.finditer trabaja sobre string original, 
            # y necesitamos saber si ya fue "consumido" (reemplazado por espacios).
            
            # Estrategia: Buscar, si valid, reemplazar con espacios en `text_norm` para no volver a matchear
            for match in re.finditer(pattern, text_norm):
                # Verificar si esta área ya fue consumida (es solo espacios?)
                # Como modificamos text_norm in-place simulado (string replacement),
                # necesitamos re-buscar en el texto modificado.
                pass 
                
            # Simplificación: 
            # Re-buscar en cada paso. Si el texto cambió, el iterador anterior puede ser inválido.
            # Mejor: Buscar 1 vez, si encuentra, extraer, agregar, y ENMASCARAR en el texto.
            
            match = re.search(pattern, text_norm)
            while match:
                start, end = match.span()
                
                # Extraer cantidad
                qty = self._extract_quantity_for_match(text_norm, start, end)
                
                # Agregar resultado
                results.append({
                    'product': product,
                    'quantity': qty,
                    'matched_text': alias # Debug info
                })
                
                # Enmascarar match encontrado con espacios para evitar re-match
                # Reemplazamos exactamente el span con espacios para mantener índices relativos de otros items
                mask_len = end - start
                text_norm = text_norm[:start] + (" " * mask_len) + text_norm[end:]
                
                # Buscar siguiente ocurrencia del MISMO alias
                match = re.search(pattern, text_norm)
                
        return results

    def parse_with_confidence(self, text: str, fuzzy_threshold: int = 70) -> List[Dict]:
        """
        Wrapper compatible para devolver formato con confianza (simulado 100% pues es match exacto/alias).
        """
        simple_results = self.parse(text)
        formatted_results = []
        for res in simple_results:
            formatted_results.append({
                'product': res['product'],
                'quantity': res['quantity'],
                'confidence': 100, # Al ser match de alias, confiamos plenamente
                'matched_text': res.get('matched_text', ''),
                'matched_to': res['product']['name']
            })
        return formatted_results
