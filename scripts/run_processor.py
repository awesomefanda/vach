"""
Main processor execution script
Runs LLM extraction on collected articles
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.llm_extractor import LLMExtractor
from src.database.operations import DatabaseOperations
from config.logging_config import get_logger

logger = get_logger(__name__)


def print_header():
    """Print script header"""
    print("=" * 60)
    print("🤖 VACH - San Jose Project Tracker")
    print("🧠 Running LLM Processing")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def check_ollama():
    """Check if Ollama is running"""
    import ollama
    try:
        ollama.list()
        print("✓ Ollama is running")
        return True
    except Exception as e:
        print("✗ Ollama is not running!")
        print("\nPlease start Ollama:")
        print("  1. Open a new terminal")
        print("  2. Run: ollama serve")
        print("  3. Then run this script again")
        return False


def print_stats(before=True):
    """Print current database statistics"""
    db = DatabaseOperations()
    stats = db.get_statistics()
    
    label = "Before Processing" if before else "After Processing"
    
    print("\n" + "=" * 60)
    print(f"📊 {label}")
    print("=" * 60)
    print(f"Total Articles:      {stats.get('total_articles', 0)}")
    print(f"  ├─ Processed:      {stats.get('processed_articles', 0)}")
    print(f"  └─ Unprocessed:    {stats.get('unprocessed_articles', 0)}")
    print(f"\nTotal Projects:      {stats.get('total_projects', 0)}")
    
    projects_by_status = stats.get('projects_by_status', {})
    if projects_by_status and sum(projects_by_status.values()) > 0:
        print("\nProjects by Status:")
        for status, count in projects_by_status.items():
            if count > 0:
                print(f"  ├─ {status.title()}: {count}")
    
    print("=" * 60)


def main():
    """Main execution function"""
    print_header()
    
    # Check Ollama
    print("\n🔍 Checking prerequisites...")
    if not check_ollama():
        return 1
    
    # Show stats before processing
    print_stats(before=True)
    
    # Check if there are articles to process
    db = DatabaseOperations()
    unprocessed = db.get_unprocessed_articles(limit=1)
    
    if not unprocessed:
        print("\n⚠️  No unprocessed articles found!")
        print("\nRun the scrapers first:")
        print("  python scripts/run_scrapers.py")
        return 0
    
    # Ask for confirmation
    stats = db.get_statistics()
    unprocessed_count = stats.get('unprocessed_articles', 0)
    
    print(f"\n📝 Found {unprocessed_count} unprocessed articles")
    print("\n⚠️  Note: LLM processing can take several minutes")
    print(f"   Estimated time: ~{unprocessed_count * 10} seconds")
    
    response = input("\nProceed with processing? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    # Run processor
    print("\n" + "=" * 60)
    print("🤖 Starting LLM Processing")
    print("=" * 60)
    print("\nThis may take a while. Processing articles...")
    
    try:
        extractor = LLMExtractor()
        
        # Process in batches
        batch_size = 10
        total_processed = 0
        total_projects = 0
        
        while True:
            results = extractor.process_unprocessed_articles(limit=batch_size)
            
            if results['processed'] == 0:
                break
            
            total_processed += results['processed']
            total_projects += results['projects_found']
            
            print(f"  Batch complete: {results['processed']} processed, {results['projects_found']} projects found")
        
        # Show results
        print("\n" + "=" * 60)
        print("✅ Processing Complete!")
        print("=" * 60)
        print(f"\nTotal articles processed: {total_processed}")
        print(f"Total projects extracted: {total_projects}")
        
        # Show updated stats
        print_stats(before=False)
        
        # Next steps
        print("\n" + "=" * 60)
        print("📝 Next Steps:")
        print("=" * 60)
        print("View results in the web interface:")
        print("  streamlit run ui/streamlit_app.py")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        print("Partial progress has been saved to the database")
        return 1
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())