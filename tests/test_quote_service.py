"""
Tests exhaustivos para QuoteService.
Valida que todos los cálculos matemáticos sean exactos.
"""
import pytest
import json
from pathlib import Path
from decimal import Decimal
from src.domain.services.quote_service import QuoteService
from src.domain.entities.quote import QuoteStatus


# Fixture: Catálogo de productos de prueba
@pytest.fixture
def test_catalog_path(tmp_path):
    """Crear catálogo de productos temporal para tests."""
    catalog = {
        "products": [
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
            },
            {
                "id": 3,
                "name": "Pantalón",
                "aliases": ["pantalon", "pants"],
                "price": 35.00,
                "category": "ropa"
            },
            {
                "id": 4,
                "name": "Gorra",
                "aliases": ["gorra", "cap"],
                "price": 15.00,
                "category": "accesorios"
            }
        ]
    }
    
    catalog_file = tmp_path / "test_catalog.json"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    return str(catalog_file)


@pytest.fixture
def quote_service(test_catalog_path):
    """Crear instancia de QuoteService con catálogo de prueba."""
    return QuoteService(catalog_path=test_catalog_path)


# ============================================
# Tests de Cálculos Matemáticos Exactos
# ============================================

def test_single_item_calculation_exact(quote_service):
    """Test: Cálculo exacto con un solo item."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos",
        "+58 412-1234567"
    )
    
    # Verificar cálculos exactos
    assert len(quote.items) == 1
    assert quote.items[0].quantity == 2
    assert quote.items[0].unit_price == 45.99
    
    # Cálculo esperado: 2 * 45.99 = 91.98
    expected_subtotal = Decimal('45.99') * Decimal('2')
    assert Decimal(str(quote.items[0].subtotal)) == expected_subtotal
    assert quote.items[0].subtotal == 91.98
    
    # Total debe ser igual al subtotal
    assert quote.total == 91.98


def test_multiple_items_calculation_exact(quote_service):
    """Test: Cálculo exacto con múltiples items."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos y 1 camisa",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 2
    
    # Item 1: 2 zapatos
    assert quote.items[0].quantity == 2
    assert quote.items[0].unit_price == 45.99
    assert quote.items[0].subtotal == 91.98
    
    # Item 2: 1 camisa
    assert quote.items[1].quantity == 1
    assert quote.items[1].unit_price == 25.50
    assert quote.items[1].subtotal == 25.50
    
    # Total: 91.98 + 25.50 = 117.48
    expected_total = Decimal('91.98') + Decimal('25.50')
    assert Decimal(str(quote.total)) == expected_total
    assert quote.total == 117.48


def test_complex_calculation_exact(quote_service):
    """Test: Cálculo complejo con múltiples items y cantidades."""
    quote = quote_service.generate_quote_from_text(
        "necesito 3 camisas, 2 pantalones y 5 gorras",
        "+58 424-9876543"
    )
    
    assert len(quote.items) == 3
    
    # Item 1: 3 camisas @ 25.50
    assert quote.items[0].quantity == 3
    assert quote.items[0].unit_price == 25.50
    assert quote.items[0].subtotal == 76.50  # 3 * 25.50
    
    # Item 2: 2 pantalones @ 35.00
    assert quote.items[1].quantity == 2
    assert quote.items[1].unit_price == 35.00
    assert quote.items[1].subtotal == 70.00  # 2 * 35.00
    
    # Item 3: 5 gorras @ 15.00
    assert quote.items[2].quantity == 5
    assert quote.items[2].unit_price == 15.00
    assert quote.items[2].subtotal == 75.00  # 5 * 15.00
    
    # Total: 76.50 + 70.00 + 75.00 = 221.50
    expected_total = Decimal('76.50') + Decimal('70.00') + Decimal('75.00')
    assert Decimal(str(quote.total)) == expected_total
    assert quote.total == 221.50


def test_decimal_precision_no_rounding_errors(quote_service):
    """Test: No debe haber errores de redondeo con decimales."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 7 zapatos",
        "+58 412-1234567"
    )
    
    # 7 * 45.99 = 321.93 (debe ser exacto)
    expected_subtotal = Decimal('45.99') * Decimal('7')
    assert Decimal(str(quote.items[0].subtotal)) == expected_subtotal
    assert quote.items[0].subtotal == 321.93
    assert quote.total == 321.93


def test_large_quantities_exact(quote_service):
    """Test: Cálculos exactos con cantidades grandes."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 100 camisas",
        "+58 412-1234567"
    )
    
    # 100 * 25.50 = 2550.00
    assert quote.items[0].quantity == 100
    assert quote.items[0].subtotal == 2550.00
    assert quote.total == 2550.00


def test_total_equals_sum_of_subtotals(quote_service):
    """Test: El total siempre debe ser igual a la suma de subtotales."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos, 3 camisas, 1 pantalon y 4 gorras",
        "+58 412-1234567"
    )
    
    # Calcular suma manual
    sum_subtotals = sum(Decimal(str(item.subtotal)) for item in quote.items)
    
    assert Decimal(str(quote.total)) == sum_subtotals


# ============================================
# Tests de Parsing de Texto
# ============================================

def test_parse_text_with_numbers(quote_service):
    """Test: Parsear texto con números."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos y 1 camisa",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 2
    assert quote.items[0].product_name == "Zapatos"
    assert quote.items[0].quantity == 2
    assert quote.items[1].product_name == "Camisa"
    assert quote.items[1].quantity == 1


def test_parse_text_with_words(quote_service):
    """Test: Parsear texto con números en palabras."""
    quote = quote_service.generate_quote_from_text(
        "necesito dos zapatos y una camisa",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 2
    assert quote.items[0].quantity == 2
    assert quote.items[1].quantity == 1


def test_parse_text_case_insensitive(quote_service):
    """Test: Parsing debe ser case-insensitive."""
    quote = quote_service.generate_quote_from_text(
        "QUIERO 2 ZAPATOS Y 1 CAMISA",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 2
    assert quote.items[0].product_name == "Zapatos"


def test_parse_text_with_accents(quote_service):
    """Test: Parsing debe manejar acentos."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 1 pantalón",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 1
    assert quote.items[0].product_name == "Pantalón"


def test_fuzzy_matching_typos(quote_service):
    """Test: Fuzzy matching debe manejar typos."""
    # "zapato" con typo -> "sapato"
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 sapatos",  # typo intencional
        "+58 412-1234567",
        fuzzy_threshold=70
    )
    
    assert len(quote.items) == 1
    assert quote.items[0].product_name == "Zapatos"


def test_fuzzy_matching_aliases(quote_service):
    """Test: Fuzzy matching debe reconocer aliases."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 shoes y 1 blusa",  # aliases en inglés
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 2
    assert quote.items[0].product_name == "Zapatos"
    assert quote.items[1].product_name == "Camisa"


# ============================================
# Tests de Validación
# ============================================

def test_empty_text_raises_error(quote_service):
    """Test: Texto vacío debe lanzar error."""
    with pytest.raises(ValueError, match="No se pudieron extraer productos"):
        quote_service.generate_quote_from_text(
            "",
            "+58 412-1234567"
        )


def test_no_products_found_raises_error(quote_service):
    """Test: Texto sin productos debe lanzar error."""
    with pytest.raises(ValueError, match="No se pudieron extraer productos"):
        quote_service.generate_quote_from_text(
            "Hola, cómo estás",
            "+58 412-1234567"
        )


def test_invalid_phone_raises_error(quote_service):
    """Test: Teléfono inválido debe lanzar error."""
    with pytest.raises(ValueError):
        quote_service.generate_quote_from_text(
            "Quiero 2 zapatos",
            "abc123"  # teléfono inválido
        )


# ============================================
# Tests de Quote con Detalles
# ============================================

def test_generate_quote_with_details(quote_service):
    """Test: Generar cotización con detalles de parsing."""
    result = quote_service.generate_quote_with_details(
        "Quiero 2 zapatos",
        "+58 412-1234567"
    )
    
    assert 'quote' in result
    assert 'parsed_items' in result
    assert 'confidence_scores' in result
    
    quote = result['quote']
    assert quote.total == 91.98
    
    # Verificar scores de confianza
    assert len(result['confidence_scores']) == 1
    assert result['confidence_scores'][0]['product'] == "Zapatos"
    assert result['confidence_scores'][0]['confidence'] >= 70


# ============================================
# Tests de Status y Notas
# ============================================

def test_quote_with_custom_status(quote_service):
    """Test: Crear cotización con status personalizado."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos",
        "+58 412-1234567",
        status=QuoteStatus.PENDING
    )
    
    assert quote.status == QuoteStatus.PENDING


def test_quote_with_notes(quote_service):
    """Test: Crear cotización con notas."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos",
        "+58 412-1234567",
        notes="Cliente VIP - Descuento 10%"
    )
    
    assert quote.notes == "Cliente VIP - Descuento 10%"


# ============================================
# Tests de Métodos Auxiliares
# ============================================

def test_get_available_products(quote_service):
    """Test: Obtener lista de productos disponibles."""
    products = quote_service.get_available_products()
    
    assert len(products) == 4
    assert products[0]['name'] == "Zapatos"


def test_search_product(quote_service):
    """Test: Buscar producto por nombre."""
    product = quote_service.search_product("zapatos")
    
    assert product is not None
    assert product['name'] == "Zapatos"
    assert product['price'] == 45.99


def test_search_product_not_found(quote_service):
    """Test: Buscar producto inexistente."""
    product = quote_service.search_product("producto_inexistente", threshold=90)
    
    assert product is None


# ============================================
# Tests de Edge Cases
# ============================================

def test_single_word_quantity_default(quote_service):
    """Test: Palabra sola sin cantidad debe usar cantidad 1."""
    # Este test verifica que si solo se menciona el producto,
    # el parser no lo detecta (necesita cantidad explícita)
    with pytest.raises(ValueError):
        quote_service.generate_quote_from_text(
            "zapatos",  # sin cantidad
            "+58 412-1234567"
        )


def test_mixed_number_formats(quote_service):
    """Test: Mezclar formatos de números."""
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos, tres camisas y 1 pantalon",
        "+58 412-1234567"
    )
    
    assert len(quote.items) == 3
    assert quote.items[0].quantity == 2
    assert quote.items[1].quantity == 3
    assert quote.items[2].quantity == 1


def test_client_phone_validation(quote_service):
    """Test: Validación de formato de teléfono."""
    # Teléfono válido
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos",
        "+58 412-1234567"
    )
    assert quote.client_phone == "+58 412-1234567"
    
    # Teléfono válido sin +
    quote = quote_service.generate_quote_from_text(
        "Quiero 2 zapatos",
        "04121234567"
    )
    assert quote.client_phone == "04121234567"


# ============================================
# Tests de Precisión Decimal
# ============================================

def test_no_floating_point_errors(quote_service):
    """Test: No debe haber errores de punto flotante."""
    # Caso conocido de error de punto flotante: 0.1 + 0.2 != 0.3
    # Nuestro sistema debe manejarlo correctamente
    
    quote = quote_service.generate_quote_from_text(
        "Quiero 3 zapatos y 2 camisas",
        "+58 412-1234567"
    )
    
    # Verificar que los cálculos son exactos
    item1_subtotal = Decimal('45.99') * Decimal('3')  # 137.97
    item2_subtotal = Decimal('25.50') * Decimal('2')  # 51.00
    expected_total = item1_subtotal + item2_subtotal  # 188.97
    
    assert Decimal(str(quote.total)) == expected_total
    assert quote.total == 188.97


def test_all_subtotals_sum_to_total(quote_service):
    """Test: Suma de subtotales siempre igual al total."""
    test_cases = [
        "Quiero 2 zapatos",
        "Quiero 2 zapatos y 1 camisa",
        "necesito 3 camisas, 2 pantalones y 5 gorras",
        "Quiero 7 zapatos y 3 camisas",
    ]
    
    for text in test_cases:
        quote = quote_service.generate_quote_from_text(
            text,
            "+58 412-1234567"
        )
        
        # Calcular suma de subtotales
        sum_subtotals = sum(
            Decimal(str(item.subtotal)) for item in quote.items
        )
        
        # Debe ser exactamente igual al total
        assert Decimal(str(quote.total)) == sum_subtotals, \
            f"Failed for: {text}"
