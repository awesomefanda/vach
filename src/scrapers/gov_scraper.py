"""
Government data scraper for San Jose
Scrapes official city websites and open data portals
"""
import sys
from pathlib import Path

# Make repo root importable when running this file directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
from src.scrapers.base_scraper import BaseScraper
from src.database.operations import DatabaseOperations
from config.settings import (
    SAN_JOSE_PRESS_URL, SAN_JOSE_OPEN_DATA_URL,
    PROJECT_KEYWORDS, MAX_ARTICLES_PER_SOURCE
)
from config.logging_config import get_logger

logger = get_logger(__name__)


class GovScraper(BaseScraper):
    """Scrapes San Jose government websites"""
    
    def __init__(self):
        super().__init__("GovScraper")
        self.db = DatabaseOperations()
    
    def scrape_press_releases(self) -> int:
        """
        Scrape San Jose press releases
        
        Returns:
            Number of press releases collected
        """
        collected = 0
        
        try:
            self.logger.info(f"Scraping press releases from {SAN_JOSE_PRESS_URL}")
            response = self.fetch_url(SAN_JOSE_PRESS_URL)
            
            if not response:
                return 0
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find press release items (adjust selectors based on actual site structure)
            # This is a template - you'll need to inspect the actual site
            articles = soup.find_all('article', limit=MAX_ARTICLES_PER_SOURCE)
            
            if not articles:
                # Try alternative selectors
                articles = soup.find_all('div', class_='news-item', limit=MAX_ARTICLES_PER_SOURCE)
            
            self.logger.info(f"Found {len(articles)} press releases")
            
            for article in articles:
                try:
                    # Extract title
                    title_elem = article.find(['h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # Check if relevant
                    if not self.contains_keywords(title, PROJECT_KEYWORDS):
                        continue
                    
                    # Extract link
                    link_elem = article.find('a')
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    url = link_elem['href']
                    if not url.startswith('http'):
                        url = f"https://www.sanjoseca.gov{url}"
                    
                    # Extract date if available
                    date_elem = article.find('time')
                    pub_date = None
                    if date_elem and date_elem.get('datetime'):
                        try:
                            pub_date = datetime.fromisoformat(
                                date_elem['datetime'].replace('Z', '+00:00')
                            )
                        except:
                            pass
                    
                    # Fetch full article content
                    full_response = self.fetch_url(url)
                    if not full_response:
                        continue
                    
                    full_soup = BeautifulSoup(full_response.content, 'html.parser')
                    
                    # Extract main content (adjust selector)
                    content_elem = full_soup.find(['article', 'div'], class_=['content', 'main-content', 'article-body'])
                    if not content_elem:
                        content_elem = full_soup.find('main')
                    
                    if not content_elem:
                        self.logger.warning(f"Could not find content for {url}")
                        continue
                    
                    text = content_elem.get_text(separator=' ', strip=True)
                    
                    # Validate and save
                    if self.validate_article_data(url, title, text):
                        article_id = self.db.add_article(
                            url=url,
                            title=title,
                            content=text,
                            source='San Jose Press Release',
                            published_date=pub_date
                        )
                        
                        if article_id:
                            collected += 1
                            self.logger.info(f"✓ Saved press release: {title[:50]}...")
                
                except Exception as e:
                    self.logger.error(f"Error processing press release: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Failed to scrape press releases: {e}")
        
        return collected
    
    def scrape_open_data(self) -> int:
        """
        Scrape San Jose Open Data portal
        Note: This is a template - actual implementation depends on available datasets
        
        Returns:
            Number of datasets processed
        """
        collected = 0
        
        try:
            self.logger.info(f"Checking San Jose Open Data: {SAN_JOSE_OPEN_DATA_URL}")
            
            # Example: Get catalog of datasets
            # This URL structure is based on Socrata platform (used by many cities)
            catalog_url = f"{SAN_JOSE_OPEN_DATA_URL}/api/catalog/v1"
            
            response = self.fetch_url(catalog_url, params={'limit': 100})
            if not response:
                self.logger.warning("Could not fetch open data catalog")
                return 0
            
            catalog = response.json()
            
            # Look for project-related datasets
            project_keywords = ['capital', 'project', 'construction', 'budget', 'infrastructure']
            
            for item in catalog.get('results', []):
                try:
                    resource = item.get('resource', {})
                    name = resource.get('name', '').lower()
                    description = resource.get('description', '').lower()
                    
                    # Check if dataset is relevant
                    if not any(kw in name or kw in description for kw in project_keywords):
                        continue
                    
                    dataset_id = resource.get('id')
                    if not dataset_id:
                        continue
                    
                    self.logger.info(f"Found relevant dataset: {resource.get('name')}")
                    
                    # Fetch dataset
                    dataset_url = f"{SAN_JOSE_OPEN_DATA_URL}/resource/{dataset_id}.json"
                    data_response = self.fetch_url(dataset_url, params={'$limit': 1000})
                    
                    if not data_response:
                        continue
                    
                    dataset = data_response.json()
                    
                    # Create an "article" summarizing the dataset
                    # This allows us to process it through the same pipeline
                    summary = f"Open Data: {resource.get('name')}\n\n"
                    summary += f"{resource.get('description', '')}\n\n"
                    summary += f"Dataset contains {len(dataset)} records.\n\n"
                    
                    # Add sample records as text
                    for record in dataset[:5]:
                        summary += f"{record}\n"
                    
                    article_id = self.db.add_article(
                        url=dataset_url,
                        title=f"Open Data: {resource.get('name')}",
                        content=summary,
                        source='San Jose Open Data',
                        published_date=datetime.utcnow()
                    )
                    
                    if article_id:
                        collected += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing dataset: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Failed to scrape open data: {e}")
        
        return collected
    
    def scrape(self) -> int:
        """
        Main scraping method
        
        Returns:
            Total number of items collected
        """
        total_collected = 0
        
        # Scrape press releases
        press_count = self.scrape_press_releases()
        total_collected += press_count
        
        # Scrape open data
        data_count = self.scrape_open_data()
        total_collected += data_count
        
        self.articles_collected = total_collected
        return total_collected


def main():
    """Run government scraper standalone"""
    scraper = GovScraper()
    
    with scraper:
        items_count = scraper.scrape()
        print(f"\n✅ Government scraping complete!")
        print(f"🏛️  Collected {items_count} items")


if __name__ == "__main__":
    main()