"""
Diagnostic helper for scrapers.

Run this to inspect RSS feeds and why articles are being filtered out.

Usage:
  python scripts/diagnose_scrapers.py
"""

import sys
from pathlib import Path

# Make repo importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import RSS_FEEDS, PROJECT_KEYWORDS, TARGET_CITY, MAX_ARTICLES_PER_SOURCE
from src.scrapers.news_scraper import NewsScraper


def check_feed(feed_url, scraper: NewsScraper, limit=10):
    print(f"\n--- Feed: {feed_url} ---")
    try:
        import feedparser
        feed = feedparser.parse(feed_url)
    except Exception as e:
        print("Failed to parse feed:", e)
        return

    print("bozo:", getattr(feed, 'bozo', False))
    entries = feed.entries[:limit]
    print(f"Found {len(entries)} entries (showing up to {limit})")

    for i, entry in enumerate(entries, 1):
        title = entry.get('title') or ''
        link = entry.get('link') or entry.get('id') or ''
        print(f"\n[{i}] {title}\n  {link}")

        # Try to parse full article via NewsScraper.parse_article
        try:
            article = scraper.parse_article(link)
        except Exception as e:
            print("  parse_article failed:", e)
            article = None

        if not article:
            print("  >> Could not download/parse article")
            continue

        text = (article.get('text') or '').strip()
        tlen = len(text)
        title_len = len(article.get('title') or '')
        print(f"  title_len={title_len} text_len={tlen}")

        # Relevance check
        combined = f"{article.get('title','')} {text}".lower()
        has_city = TARGET_CITY.lower() in combined
        has_keyword = any(kw.lower() in combined for kw in PROJECT_KEYWORDS)
        print(f"  contains target city: {has_city}")
        print(f"  contains project keywords: {has_keyword}")

        # Validation via BaseScraper.validate_article_data
        valid = scraper.validate_article_data(article.get('url'), article.get('title'), text)
        print(f"  passes validate_article_data: {valid}")
        if not valid:
            # show short reasons by re-checking thresholds
            if not article.get('url') or not str(article.get('url')).startswith('http'):
                print("    reason: invalid url")
            if not article.get('title') or len(article.get('title')) < 10:
                print("    reason: title too short (<10)")
            if not text or len(text) < 100:
                print("    reason: text too short (<100)")


def main():
    print("Scraper diagnostic started")
    scraper = NewsScraper()

    for feed in RSS_FEEDS:
        check_feed(feed, scraper, limit=min(10, MAX_ARTICLES_PER_SOURCE))

    print("\nDiagnostic complete. Review above output for reasons entries are filtered.")


if __name__ == '__main__':
    main()
