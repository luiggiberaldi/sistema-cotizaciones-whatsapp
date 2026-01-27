"""
Tests para la entidad Quote.
"""
import pytest
from datetime import datetime
from src.domain.entities.quote import Quote, QuoteItem, QuoteStatus


def test_create_quote_item():
    """Test crear un item de cotización válido."""
    item = QuoteItem(
        product_name="Laptop",
        quantity=2,
        unit_price=1000.00,
        subtotal=2000.00
    )
    
    assert item.product_name == "Laptop"
    assert item.quantity == 2
    assert item.unit_price == 1000.00
    assert item.subtotal == 2000.00


def test_quote_item_invalid_subtotal():
    """Test que el subtotal debe coincidir con cantidad * precio."""
    with pytest.raises(ValueError):
        QuoteItem(
            product_name="Laptop",
            quantity=2,
            unit_price=1000.00,
            subtotal=1500.00  # Incorrecto
        )


def test_create_quote():
    """Test crear una cotización válida."""
    items = [
        QuoteItem(
            product_name="Laptop",
            quantity=1,
            unit_price=1200.00,
            subtotal=1200.00
        )
    ]
    
    quote = Quote(
        client_phone="+58 412-1234567",
        items=items,
        total=1200.00,
        status=QuoteStatus.DRAFT
    )
    
    assert quote.client_phone == "+58 412-1234567"
    assert len(quote.items) == 1
    assert quote.total == 1200.00
    assert quote.status == QuoteStatus.DRAFT


def test_quote_invalid_total():
    """Test que el total debe coincidir con la suma de subtotales."""
    items = [
        QuoteItem(
            product_name="Laptop",
            quantity=1,
            unit_price=1200.00,
            subtotal=1200.00
        )
    ]
    
    with pytest.raises(ValueError):
        Quote(
            client_phone="+58 412-1234567",
            items=items,
            total=1000.00,  # Incorrecto
            status=QuoteStatus.DRAFT
        )


def test_quote_calculate_total():
    """Test calcular el total de una cotización."""
    items = [
        QuoteItem(
            product_name="Laptop",
            quantity=2,
            unit_price=1200.00,
            subtotal=2400.00
        ),
        QuoteItem(
            product_name="Mouse",
            quantity=2,
            unit_price=50.00,
            subtotal=100.00
        )
    ]
    
    quote = Quote(
        client_phone="+58 412-1234567",
        items=items,
        total=2500.00,
        status=QuoteStatus.DRAFT
    )
    
    assert quote.calculate_total() == 2500.00


def test_quote_invalid_phone():
    """Test validación de formato de teléfono."""
    items = [
        QuoteItem(
            product_name="Laptop",
            quantity=1,
            unit_price=1200.00,
            subtotal=1200.00
        )
    ]
    
    with pytest.raises(ValueError):
        Quote(
            client_phone="abc123",  # Formato inválido
            items=items,
            total=1200.00,
            status=QuoteStatus.DRAFT
        )


def test_quote_add_item():
    """Test agregar un item a una cotización."""
    items = [
        QuoteItem(
            product_name="Laptop",
            quantity=1,
            unit_price=1200.00,
            subtotal=1200.00
        )
    ]
    
    quote = Quote(
        client_phone="+58 412-1234567",
        items=items,
        total=1200.00,
        status=QuoteStatus.DRAFT
    )
    
    new_item = QuoteItem(
        product_name="Mouse",
        quantity=1,
        unit_price=50.00,
        subtotal=50.00
    )
    
    quote.add_item(new_item)
    
    assert len(quote.items) == 2
    assert quote.total == 1250.00
