"""
Orchestration script to run all configured scrapers in `src/scrapers/`.

This script imports available scraper classes (News, Gov, YouTube) and
executes them one-by-one using their context manager support. It logs
results and continues if a single scraper fails.
"""

import sys
from pathlib import Path

# Ensure repo root is importable when running this script directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logging_config import get_logger

logger = get_logger(__name__)


def load_scrapers():
    scrapers = []

    # Import scrapers if present; keep going if any import fails
    try:
        from src.scrapers.news_scraper import NewsScraper
        scrapers.append(NewsScraper())
    except Exception as e:
        logger.warning(f"NewsScraper not available: {e}")

    try:
        from src.scrapers.gov_scraper import GovScraper
        scrapers.append(GovScraper())
    except Exception as e:
        logger.warning(f"GovScraper not available: {e}")

    try:
        from src.scrapers.youtube_scraper import YoutubeScraper
        scrapers.append(YoutubeScraper())
    except Exception:
        # optional scraper; ignore if missing
        pass

    return scrapers


def main():
    logger.info("Starting scraper runner")

    scrapers = load_scrapers()
    if not scrapers:
        logger.info("No scrapers found. Ensure src/scrapers contains scraper modules.")
        print("No scrapers available to run.")
        return 0

    total_collected = 0

    for scraper in scrapers:
        try:
            with scraper:
                collected = scraper.scrape()
                total_collected += collected or 0
                logger.info(f"{scraper.name}: collected {collected}")
                print(f"{scraper.name}: collected {collected}")
        except KeyboardInterrupt:
            logger.warning("Scraper run interrupted by user")
            print("Interrupted.")
            return 1
        except Exception as e:
            logger.error(f"Error running {getattr(scraper, 'name', scraper.__class__.__name__)}: {e}", exc_info=True)
            print(f"Error running {getattr(scraper, 'name', scraper.__class__.__name__)}: {e}")
            # continue to next scraper

    logger.info(f"Scraping complete. Total items collected: {total_collected}")
    print(f"Scraping complete. Total items collected: {total_collected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
