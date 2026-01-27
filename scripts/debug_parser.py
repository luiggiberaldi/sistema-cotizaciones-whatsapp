import re
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.services.text_parser import TextParser

def test_parser():
    # Mock catalog
    catalog = [
        {"name": "Zapatos", "aliases": ["zapato", "calzado", "pares"], "price": 10},
        {"name": "Camisa", "aliases": ["camisa"], "price": 5}
    ]
    
    parser = TextParser(catalog)
    text = "Hola, quiero 3 pares de zapatos y 2 camisas por favor"
    
    print(f"Texto: '{text}'")
    print("-" * 20)
    
    # Test internal regex
    print("Probando Regex Interno:")
    parser_regex = r'(\d+|un|una|uno|dos|tres)\s+(?:(?:pares|unidades|piezas|cajas|paquetes|botellas|kilos|gramos|litros|de)\s+)*([a-z]+)'
    
    normalized = parser._normalize_text(text)
    print(f"Normalizado: '{normalized}'")
    
    matches = re.finditer(parser_regex, normalized)
    for m in matches:
        print(f"Match: '{m.group(0)}' -> Cantidad: '{m.group(1)}', Producto: '{m.group(2)}'")
        
    print("-" * 20)
    print("Probando Parse Completo:")
    results = parser.parse(text)
    print(f"Resultados: {results}")

if __name__ == "__main__":
    test_parser()
