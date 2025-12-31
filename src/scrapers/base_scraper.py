"""
Base scraper class with common functionality
Provides retry logic, rate limiting, and error handling
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import (
    REQUEST_TIMEOUT, RETRY_ATTEMPTS, RATE_LIMIT_DELAY, USER_AGENT
)
from config.logging_config import get_logger

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, name: str):
        """
        Initialize base scraper
        
        Args:
            name: Scraper name for logging
        """
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.articles_collected = 0
        self.start_time = None
    
    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_url(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Fetch a URL with retry logic
        
        Args:
            url: URL to fetch
            params: Optional query parameters
            
        Returns:
            Response object or None if failed
        """
        try:
            self.logger.debug(f"Fetching: {url}")
            response = self.session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            return response
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout fetching {url}")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    def start_run(self):
        """Start tracking scraper run"""
        self.start_time = time.time()
        self.articles_collected = 0
        self.logger.info(f"Starting {self.name} scraper")
    
    def end_run(self, success: bool = True, error_message: Optional[str] = None):
        """
        End scraper run and log results
        
        Args:
            success: Whether the run was successful
            error_message: Optional error message
        """
        duration = time.time() - self.start_time if self.start_time else 0
        
        self.logger.info(
            f"{self.name} scraper finished: "
            f"{self.articles_collected} articles collected in {duration:.2f}s"
        )
        
        # Log to database
        from src.database.operations import DatabaseOperations
        DatabaseOperations.log_scraper_run(
            scraper_name=self.name,
            articles_collected=self.articles_collected,
            success=success,
            duration=duration,
            error_message=error_message
        )
    
    def contains_keywords(self, text: str, keywords: list) -> bool:
        """
        Check if text contains any of the specified keywords
        
        Args:
            text: Text to search
            keywords: List of keywords
            
        Returns:
            True if any keyword found
        """
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def validate_article_data(self, url: str, title: str, text: str) -> bool:
        """
        Validate article data before saving
        
        Args:
            url: Article URL
            title: Article title
            text: Article text
            
        Returns:
            True if valid
        """
        if not url or not url.startswith('http'):
            self.logger.warning(f"Invalid URL: {url}")
            return False
        
        if not title or len(title) < 10:
            self.logger.warning(f"Title too short: {title}")
            return False
        
        if not text or len(text) < 100:
            self.logger.warning(f"Text too short for {url}")
            return False
        
        return True
    
    @abstractmethod
    def scrape(self) -> int:
        """
        Main scraping method to be implemented by subclasses
        
        Returns:
            Number of articles collected
        """
        pass
    
    def __enter__(self):
        """Context manager entry"""
        self.start_run()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.end_run(success=False, error_message=str(exc_val))
        else:
            self.end_run(success=True)