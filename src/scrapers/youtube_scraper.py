
"""
Placeholder YouTube scraper.
"""

import sys
from pathlib import Path

# Make repo root importable when running this file directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class YoutubeScraper:
	def __init__(self):
		self.name = 'YoutubeScraper'

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc, tb):
		return False

	def scrape(self):
		# No-op placeholder
		return 0
