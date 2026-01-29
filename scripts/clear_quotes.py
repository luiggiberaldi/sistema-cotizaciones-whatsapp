import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config.database import get_supabase_client

def clear_all_quotes(force=False):
    print("="*60)
    print("CLEANING UP QUOTES TABLE")
    print("="*60)
    
    if not force:
        print("WARNING: This will DELETE ALL QUOTES from the database.")
        print("This is for DEMO purposes only.")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != 'DELETE':
            print("Operation cancelled.")
            return

    client = get_supabase_client()
    try:
        # Delete all rows where id is not 0 (assuming auto-increment starts at 1)
        response = client.table("quotes").delete().neq("id", 0).execute()
        print(f"✅ Successfully deleted all quotes.")
    except Exception as e:
        print(f"❌ Error deleting quotes: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='Skip confirmation')
    args = parser.parse_args()
    clear_all_quotes(args.force)
