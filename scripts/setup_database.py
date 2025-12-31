"""
Database initialization script
Run this first to create the database and tables
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import init_database
from config.logging_config import get_logger
from config.settings import DATABASE_PATH

logger = get_logger(__name__)


def main():
    """Initialize the Vach database"""
    print("🗄️  Initializing Vach database...")
    print(f"📍 Location: {DATABASE_PATH}")
    
    try:
        success = init_database()
        
        if success:
            print("\n✅ Database initialized successfully!")
            print("\nTables created:")
            print("  - articles")
            print("  - projects")
            print("  - project_updates")
            print("  - scraper_runs")
            print("\nYou can now run the scrapers:")
            print("  python scripts/run_scrapers.py")
            return 0
        else:
            print("\n❌ Failed to initialize database")
            print("Check logs for details")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())