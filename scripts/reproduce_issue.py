
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from domain.entities.quote import Quote, QuoteItem, QuoteStatus
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_quote_creation():
    print("Testing Quote creation...")
    
    item = QuoteItem(
        product_name="Test Product",
        quantity=1,
        unit_price=10.0,
        subtotal=10.0
    )
    
    try:
        quote = Quote(
            id=1,
            client_phone="+1234567890",
            items=[item],
            total=10.0,
            status=QuoteStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            notes=None,
            customer_id=None,
            client_name="Test Client",
            client_dni="123456",
            client_address="Test Address"
        )
        print("Quote created successfully!")
        print(quote.model_dump())
    except Exception as e:
        print(f"Caught expected exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quote_creation()
