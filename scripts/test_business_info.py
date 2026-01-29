"""
Test script for Business Info module
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.business_info_repository import BusinessInfoRepository
from src.infrastructure.services.business_info_service import BusinessInfoService

def test_repository():
    """Test the repository directly"""
    print("=" * 60)
    print("Testing Business Info Repository")
    print("=" * 60)
    
    repo = BusinessInfoRepository()
    
    # Get all business info
    data = repo.get_all()
    print(f"\nFound {len(data)} business info records:")
    
    for item in data:
        print(f"\n  Key: {item.key}")
        print(f"  Value: {item.value}")
        print(f"  Category: {item.category}")
        print(f"  Active: {item.is_active}")
    
    return data

def test_service():
    """Test the service with caching"""
    print("\n" + "=" * 60)
    print("Testing Business Info Service (with caching)")
    print("=" * 60)
    
    service = BusinessInfoService()
    
    # First call (should hit DB)
    print("\nFirst call (cache miss)...")
    data1 = service.get_all_info()
    print(f"Retrieved {len(data1)} records")
    
    # Second call (should hit cache)
    print("\nSecond call (cache hit)...")
    data2 = service.get_all_info()
    print(f"Retrieved {len(data2)} records")
    
    # Test getting by key
    print("\nTesting get_by_key...")
    address = service.get_info_by_key('direccion')
    if address:
        print(f"Address: {address.value}")
    
    return data1

if __name__ == "__main__":
    try:
        # Test repository
        repo_data = test_repository()
        
        # Test service
        service_data = test_service()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
