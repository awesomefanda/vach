"""
LLM-based project extraction from articles
Uses Ollama for local inference
"""

import json
import re
from typing import Optional, Dict, Any
import ollama
from config.settings import (
    OLLAMA_MODEL, OLLAMA_HOST, LLM_MAX_TOKENS, 
    LLM_TEMPERATURE, TARGET_CITY, PROJECT_TYPES
)
from config.logging_config import get_logger
from src.database.operations import DatabaseOperations

logger = get_logger(__name__)


class LLMExtractor:
    """Extracts structured project data from unstructured text using LLM"""
    
    EXTRACTION_PROMPT = """You are analyzing city government and news articles about San Jose, California projects.

Extract project information and return ONLY valid JSON with no markdown formatting or explanations.

Required JSON structure:
{{
  "project_name": "exact name of the project",
  "location": "specific San Jose neighborhood, district, or address",
  "project_type": "one of: housing, transit, infrastructure, parks, public_safety, other",
  "promised_completion": "completion date if mentioned (YYYY-MM-DD format), else null",
  "budget": "dollar amount if mentioned (include $, e.g. '$5 million'), else null",
  "official": "name of mayor/council member/official who announced, else null",
  "status": "one of: announced, approved, in_progress, delayed, completed, cancelled",
  "description": "single sentence summary of the project"
}}

Rules:
1. Return ONLY the JSON object, no other text
2. Use null for missing information
3. Be precise with dates and amounts
4. Keep description under 150 characters
5. If no clear project is mentioned, return: {{"project_name": null}}

Article text:
{article_text}

JSON output:"""
    
    def __init__(self):
        """Initialize LLM extractor"""
        self.model = OLLAMA_MODEL
        self.host = OLLAMA_HOST
        self.db = DatabaseOperations()
        self.logger = get_logger(__name__)
        
        # Test Ollama connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama"""
        try:
            ollama.list()
            self.logger.info(f"✓ Connected to Ollama at {self.host}")
        except Exception as e:
            self.logger.error(f"✗ Failed to connect to Ollama: {e}")
            self.logger.error(f"Make sure Ollama is running: ollama serve")
            raise
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean LLM response to extract valid JSON
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Remove any text before first {
        start_idx = response.find('{')
        if start_idx > 0:
            response = response[start_idx:]
        
        # Remove any text after last }
        end_idx = response.rfind('}')
        if end_idx > 0:
            response = response[:end_idx + 1]
        
        return response.strip()
    
    def extract_from_text(self, text: str, article_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract project information from text using LLM
        
        Args:
            text: Article text to analyze
            article_url: Optional source URL for logging
            
        Returns:
            Dictionary with extracted project data or None if failed
        """
        try:
            # Truncate text to fit context window
            truncated_text = text[:LLM_MAX_TOKENS * 3]  # Rough character estimate
            
            # Format prompt
            prompt = self.EXTRACTION_PROMPT.format(article_text=truncated_text)
            
            self.logger.debug(f"Sending {len(truncated_text)} chars to LLM")
            
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': LLM_TEMPERATURE,
                    'num_predict': 500,
                }
            )
            
            # Extract response
            response_text = response['response']
            self.logger.debug(f"Raw LLM response: {response_text[:200]}...")
            
            # Clean and parse JSON
            cleaned_json = self._clean_json_response(response_text)
            project_data = json.loads(cleaned_json)
            
            # Validate we got a project
            if not project_data.get('project_name'):
                self.logger.debug("No project found in article")
                return None
            
            # Add metadata
            project_data['source_url'] = article_url
            project_data['extraction_confidence'] = self._calculate_confidence(project_data)
            
            self.logger.info(f"✓ Extracted project: {project_data['project_name']}")
            return project_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from LLM response: {e}")
            self.logger.debug(f"Attempted to parse: {cleaned_json}")
            return None
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {e}")
            return None
    
    def _calculate_confidence(self, project_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on completeness of data
        
        Args:
            project_data: Extracted project data
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        total_fields = 8
        
        # Check each field
        if project_data.get('project_name'):
            score += 1
        if project_data.get('location'):
            score += 1
        if project_data.get('project_type') in PROJECT_TYPES:
            score += 1
        if project_data.get('description'):
            score += 1
        if project_data.get('promised_completion'):
            score += 1
        if project_data.get('budget'):
            score += 1
        if project_data.get('official'):
            score += 1
        if project_data.get('status'):
            score += 1
        
        return round(score / total_fields, 2)
    
    def process_article(self, article_id: int, article_text: str, article_url: str) -> bool:
        """
        Process a single article and save extracted project
        
        Args:
            article_id: Database article ID
            article_text: Article text
            article_url: Article URL
            
        Returns:
            True if successful
        """
        try:
            # Extract project data
            project_data = self.extract_from_text(article_text, article_url)
            
            if not project_data:
                # Mark as processed even if no project found
                self.db.mark_article_processed(article_id, error="No project data extracted")
                return False
            
            # Check for duplicate projects
            similar_projects = self.db.find_similar_projects(
                project_data['project_name'],
                project_data.get('location', '')
            )
            
            if similar_projects:
                self.logger.info(f"Found {len(similar_projects)} similar projects")
                # TODO: Implement smart merging logic
                # For now, we'll add as update to first similar project
                project_id = similar_projects[0].id
                self.db.add_project_update(
                    project_id=project_id,
                    status=project_data.get('status', 'announced'),
                    source_url=article_url,
                    source_type='news',
                    notes=project_data.get('description')
                )
            else:
                # Add as new project
                project_data['confidence_score'] = project_data.pop('extraction_confidence', 1.0)
                project_id = self.db.add_project(project_data)
                
                if project_id:
                    # Add initial update
                    self.db.add_project_update(
                        project_id=project_id,
                        status=project_data.get('status', 'announced'),
                        source_url=article_url,
                        source_type='news',
                        notes=f"Initial discovery from {article_url}"
                    )
            
            # Mark article as processed
            self.db.mark_article_processed(article_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process article {article_id}: {e}")
            self.db.mark_article_processed(article_id, error=str(e))
            return False
    
    def process_unprocessed_articles(self, limit: int = 20) -> Dict[str, int]:
        """
        Process all unprocessed articles in the database
        
        Args:
            limit: Maximum number of articles to process
            
        Returns:
            Dictionary with processing statistics
        """
        articles = self.db.get_unprocessed_articles(limit=limit)
        
        if not articles:
            self.logger.info("No unprocessed articles found")
            return {'processed': 0, 'projects_found': 0, 'failed': 0}
        
        self.logger.info(f"Processing {len(articles)} articles...")
        
        processed = 0
        projects_found = 0
        failed = 0
        
        for article in articles:
            self.logger.info(f"Processing: {article.title[:50]}...")
            
            success = self.process_article(
                article.id,
                article.text,
                article.url
            )
            
            if success:
                processed += 1
                projects_found += 1
            else:
                processed += 1
        
        stats = {
            'processed': processed,
            'projects_found': projects_found,
            'failed': failed
        }
        
        self.logger.info(f"Processing complete: {stats}")
        return stats


def main():
    """Run LLM extractor standalone"""
    print("🤖 Starting LLM Extraction...")
    
    extractor = LLMExtractor()
    stats = extractor.process_unprocessed_articles(limit=10)
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Processed: {stats['processed']}")
    print(f"🎯 Projects found: {stats['projects_found']}")
    print(f"❌ Failed: {stats['failed']}")


if __name__ == "__main__":
    main()