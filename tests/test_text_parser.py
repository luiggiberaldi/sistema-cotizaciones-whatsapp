"""
Tests para TextParser.
"""
import pytest
import json
from pathlib import Path
from src.domain.services.text_parser import TextParser


@pytest.fixture
def test_catalog():
    """Catálogo de productos para tests."""
    return [
        {
            "id": 1,
            "name": "Zapatos",
            "aliases": ["zapato", "calzado", "shoes"],
            "price": 45.99,
            "category": "calzado"
        },
        {
            "id": 2,
            "name": "Camisa",
            "aliases": ["camisa", "blusa", "shirt"],
            "price": 25.50,
            "category": "ropa"
        }
    ]


@pytest.fixture
def parser(test_catalog):
    """Crear instancia de TextParser."""
    return TextParser(test_catalog)


def test_parse_simple_text(parser):
    """Test: Parsear texto simple."""
    results = parser.parse("Quiero 2 zapatos")
    
    assert len(results) == 1
    assert results[0]['quantity'] == 2
    assert results[0]['product']['name'] == "Zapatos"


def test_parse_multiple_items(parser):
    """Test: Parsear múltiples items."""
    results = parser.parse("Quiero 2 zapatos y 1 camisa")
    
    assert len(results) == 2
    assert results[0]['quantity'] == 2
    assert results[0]['product']['name'] == "Zapatos"
    assert results[1]['quantity'] == 1
    assert results[1]['product']['name'] == "Camisa"


def test_parse_with_word_numbers(parser):
    """Test: Parsear con números en palabras."""
    results = parser.parse("necesito dos zapatos y una camisa")
    
    assert len(results) == 2
    assert results[0]['quantity'] == 2
    assert results[1]['quantity'] == 1


def test_fuzzy_matching(parser):
    """Test: Fuzzy matching con typos."""
    results = parser.parse("Quiero 2 sapatos")  # typo
    
    assert len(results) == 1
    assert results[0]['product']['name'] == "Zapatos"


def test_parse_with_confidence(parser):
    """Test: Parsear con scores de confianza."""
    results = parser.parse_with_confidence("Quiero 2 zapatos")
    
    assert len(results) == 1
    assert results[0]['quantity'] == 2
    assert results[0]['confidence'] >= 70
    assert 'matched_text' in results[0]
    assert 'matched_to' in results[0]


def test_normalize_text(parser):
    """Test: Normalización de texto."""
    normalized = parser._normalize_text("ZAPATOS con Ácentos")
    
    assert normalized == "zapatos con acentos"


def test_empty_text(parser):
    """Test: Texto vacío."""
    results = parser.parse("")
    
    assert len(results) == 0


def test_no_products_found(parser):
    """Test: Texto sin productos."""
    results = parser.parse("Hola, cómo estás")
    
    assert len(results) == 0
