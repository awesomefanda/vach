"""
Test DB write: attempts to insert a sample article and reports success/failure.
Run: python scripts/test_db_write.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.operations import DatabaseOperations


def main():
    db = DatabaseOperations()
    sample = {
        'url': 'https://example.test/vach-sample-123',
        'title': 'Vach sample test article',
        'text': 'This is a test article body. ' * 10,
        'source': 'test',
    }

    print('Attempting to add sample article...')
    aid = db.add_article(sample['url'], sample['title'], sample['text'], sample['source'])
    if aid:
        print('Article inserted with id', aid)
    else:
        print('Article insert returned None (likely duplicate or error).')

    # Show counts
    stats = db.get_statistics()
    print('DB stats:', stats)


if __name__ == '__main__':
    main()
