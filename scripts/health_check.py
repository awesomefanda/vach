"""
System health check script
Verifies all components are working correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logging_config import get_logger
from config.settings import DATABASE_PATH, LOG_DIR_PATH
import ollama
import requests

logger = get_logger(__name__)


def print_header():
    """Print header"""
    print("=" * 60)
    print("🏥 VACH SYSTEM HEALTH CHECK")
    print("=" * 60)


def check_python_version():
    """Check Python version"""
    print("\n📍 Checking Python version...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro}")
        print("   Python 3.8+ required")
        return False


def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required = [
        'requests', 'beautifulsoup4', 'feedparser', 'newspaper3k',
        'sqlalchemy', 'ollama', 'streamlit', 'pandas', 'plotly'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_').replace('3k', ''))
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n   Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def check_ollama():
    """Check if Ollama is running"""
    print("\n🤖 Checking Ollama...")
    
    try:
        models = ollama.list()
        print("   ✓ Ollama is running")
        
        # Check for required model
        model_names = [m['name'] for m in models.get('models', [])]
        
        if any('qwen' in name.lower() or 'llama' in name.lower() for name in model_names):
            print(f"   ✓ LLM models available: {len(model_names)}")
            return True
        else:
            print("   ⚠ No compatible models found")
            print("   Run: ollama pull qwen2.5-coder:7b")
            return False
            
    except Exception as e:
        print(f"   ✗ Ollama not running")
        print(f"   Error: {e}")
        print("   Start Ollama: ollama serve")
        return False


def check_database():
    """Check if database exists and is accessible"""
    print("\n🗄️  Checking database...")
    
    db_path = Path(DATABASE_PATH)
    
    if not db_path.exists():
        print(f"   ✗ Database not found at {DATABASE_PATH}")
        print("   Run: python scripts/setup_database.py")
        return False
    
    try:
        from src.database.models import get_session, close_session
        session = get_session()
        close_session(session)
        print(f"   ✓ Database accessible at {DATABASE_PATH}")
        return True
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False


def check_directories():
    """Check if required directories exist"""
    print("\n📁 Checking directories...")
    
    required_dirs = [
        Path(DATABASE_PATH).parent,
        Path(LOG_DIR_PATH),
        Path(DATABASE_PATH).parent / "raw",
        Path(DATABASE_PATH).parent / "processed"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if directory.exists():
            print(f"   ✓ {directory}")
        else:
            print(f"   ⚠ {directory} (will be created)")
            directory.mkdir(parents=True, exist_ok=True)
    
    return all_exist


def check_internet():
    """Check internet connectivity"""
    print("\n🌐 Checking internet connectivity...")
    
    test_urls = [
        "https://www.mercurynews.com",
        "https://sanjosespotlight.com",
        "https://www.sanjoseca.gov"
    ]
    
    working = 0
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✓ {url}")
                working += 1
            else:
                print(f"   ⚠ {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"   ✗ {url} (Error: {e})")
    
    return working > 0


def check_config():
    """Check if configuration is valid"""
    print("\n⚙️  Checking configuration...")
    
    from config.settings import (
        RSS_FEEDS, PROJECT_KEYWORDS, TARGET_CITY, OLLAMA_MODEL
    )
    
    print(f"   ✓ Target city: {TARGET_CITY}")
    print(f"   ✓ LLM model: {OLLAMA_MODEL}")
    print(f"   ✓ RSS feeds: {len(RSS_FEEDS)}")
    print(f"   ✓ Keywords: {len(PROJECT_KEYWORDS)}")
    
    return True


def main():
    """Run all health checks"""
    print_header()
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Ollama': check_ollama(),
        'Database': check_database(),
        'Directories': check_directories(),
        'Internet': check_internet(),
        'Configuration': check_config()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nYou're ready to run Vach:")
        print("  1. python scripts/run_scrapers.py")
        print("  2. python scripts/run_processor.py")
        print("  3. streamlit run ui/streamlit_app.py")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running Vach")
        return 1
    
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())