"""
News scraper using RSS feeds and newspaper3k
Scrapes local news sources for San Jose project coverage
"""
import sys
from pathlib import Path

# Make repo root importable when running this file directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import feedparser
from newspaper import Article
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from src.scrapers.base_scraper import BaseScraper
from src.database.operations import DatabaseOperations
from config.settings import (
    RSS_FEEDS, PROJECT_KEYWORDS, TARGET_CITY, MAX_ARTICLES_PER_SOURCE,
    USER_AGENT, REQUEST_TIMEOUT
)

from config.settings import SCRAPER_DEBUG
from config.logging_config import get_logger

logger = get_logger(__name__)


class NewsScraper(BaseScraper):
    """Scrapes news articles from RSS feeds"""
    
    def __init__(self):
        super().__init__("NewsScraper")
        self.rss_feeds = RSS_FEEDS
        self.keywords = PROJECT_KEYWORDS
        self.db = DatabaseOperations()
    
    def parse_article(self, url: str) -> dict:
        """
        Parse full article content from URL
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary with article data or None if failed
        """
        # Primary: try newspaper3k
        title = None
        text = None
        publish_date = None
        authors = None

        try:
            article = Article(url)
            article.download()
            article.parse()
            title = article.title
            text = article.text
            publish_date = article.publish_date
            authors = article.authors
        except Exception as e:
            self.logger.debug(f"newspaper3k parse failed for {url}: {e}")

        # Fallback: requests + BeautifulSoup when newspaper3k fails or text is empty
        if not text or len((text or '').strip()) < 200:
            try:
                headers = {'User-Agent': USER_AGENT}
                resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Try to extract title if missing
                if not title:
                    t = soup.find('title')
                    title = t.get_text(strip=True) if t else None

                # Collect paragraph text
                paragraphs = soup.find_all('p')
                para_texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                if para_texts:
                    text = '\n\n'.join(para_texts)

                # Try common meta tags for publish date
                if not publish_date:
                    meta = soup.find('meta', {'property': 'article:published_time'}) or soup.find('meta', {'name': 'pubdate'})
                    if meta and meta.get('content'):
                        try:
                            from dateutil import parser as dateparser
                            publish_date = dateparser.parse(meta.get('content'))
                        except Exception:
                            publish_date = None

            except Exception as e:
                self.logger.debug(f"HTML fallback parse failed for {url}: {e}")

        if not title and not text:
            self.logger.warning(f"Failed to parse article {url}: no title/text")
            return None

        return {
            'url': url,
            'title': title,
            'text': text or '',
            'publish_date': publish_date,
            'authors': authors or []
        }
    
    def is_relevant_article(self, title: str, text: str) -> bool:
        """
        Check if article is relevant to San Jose projects
        
        Args:
            title: Article title
            text: Article text
            
        Returns:
            True if relevant
        """
        # If debug mode is enabled, treat everything as relevant for testing
        if SCRAPER_DEBUG:
            return True

        # Must mention San Jose
        combined_text = f"{title} {text}".lower()
        if TARGET_CITY.lower() not in combined_text:
            return False
        
        # Must contain project keywords
        if not self.contains_keywords(combined_text, self.keywords):
            return False
        
        return True
    
    def scrape_feed(self, feed_url: str, source_name: str) -> int:
        """
        Scrape a single RSS feed
        
        Args:
            feed_url: RSS feed URL
            source_name: Name of the source
            
        Returns:
            Number of articles collected
        """
        collected = 0
        
        try:
            self.logger.info(f"Scraping feed: {source_name}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                self.logger.warning(f"Feed parsing had issues: {feed_url}")
            
            entries = feed.entries[:MAX_ARTICLES_PER_SOURCE]
            self.logger.info(f"Found {len(entries)} entries in {source_name}")
            
            for entry in entries:
                try:
                    # Check if already in database
                    if not entry.get('link'):
                        continue
                    
                    # Parse full article
                    article_data = self.parse_article(entry.link)
                    if not article_data:
                        continue
                    
                    # Check relevance
                    if not self.is_relevant_article(
                        article_data['title'], 
                        article_data['text']
                    ):
                        self.logger.debug(
                            f"Article not relevant: {article_data['title'][:50]}"
                        )
                        continue
                    
                    # Validate data
                    if not self.validate_article_data(
                        article_data['url'],
                        article_data['title'],
                        article_data['text']
                    ):
                        continue
                    
                    # Save to database
                    article_id = self.db.add_article(
                        url=article_data['url'],
                        title=article_data['title'],
                        content=article_data['text'],
                        source=source_name,
                        published_date=article_data.get('publish_date')
                    )
                    
                    if article_id:
                        collected += 1
                        self.logger.info(
                            f"✓ Saved: {article_data['title'][:60]}..."
                        )
                    
                except Exception as e:
                    self.logger.error(f"Error processing entry: {e}")
                    continue
            
            self.logger.info(f"Collected {collected} articles from {source_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to scrape feed {feed_url}: {e}")
        
        return collected
    
    def scrape(self) -> int:
        """
        Main scraping method
        
        Returns:
            Total number of articles collected
        """
        total_collected = 0
        
        for feed_url in self.rss_feeds:
            # Extract source name from URL
            source_name = feed_url.split('/')[2].replace('www.', '')
            
            collected = self.scrape_feed(feed_url, source_name)
            total_collected += collected
        
        self.articles_collected = total_collected
        return total_collected


def main():
    """Run news scraper standalone"""
    scraper = NewsScraper()
    
    with scraper:
        articles_count = scraper.scrape()
        print(f"\n✅ News scraping complete!")
        print(f"📰 Collected {articles_count} relevant articles")


if __name__ == "__main__":
    main()