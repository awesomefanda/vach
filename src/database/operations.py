"""
Database operation helpers used by scrapers and processors.
Provides a `DatabaseOperations` class with convenience methods.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func
import sqlalchemy as sa
import sqlite3
from src.database.models import (
    get_session, close_session, Article, Project, ProjectUpdate, ScraperRun
)
from types import SimpleNamespace
from config.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseOperations:
    """Helper wrapper around SQLAlchemy session for common operations."""

    def __init__(self):
        self.session = get_session()
        # Ensure DB schema has required columns (lightweight migration)
        try:
            self._ensure_schema()
        except Exception:
            # Don't fail initialization for schema issues; operations will surface errors
            pass
        # Detect presence of processed column to support older DBs
        try:
            cols = self._get_table_columns('articles')
            self.table_columns = set(cols)
            self.has_processed = 'processed' in self.table_columns
        except Exception:
            self.table_columns = set()
            self.has_processed = False

    def _get_table_columns(self, table_name: str) -> List[str]:
        # Use sqlite3 PRAGMA directly to avoid SQLAlchemy/session quirks
        try:
            from config.settings import DATABASE_PATH
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info('{table_name}')")
            rows = cur.fetchall()
            conn.close()
            return [row[1] for row in rows]
        except Exception:
            return []

    def _add_column_if_missing(self, table: str, column_name: str, column_def: str):
        cols = self._get_table_columns(table)
        if column_name not in cols:
            try:
                self.session.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
                self.session.commit()
            except Exception:
                self.session.rollback()

    def _ensure_schema(self):
        # Articles
        self._add_column_if_missing('articles', 'text', 'TEXT')
        self._add_column_if_missing('articles', 'processed', 'INTEGER DEFAULT 0')
        self._add_column_if_missing('articles', 'processed_at', 'DATETIME')
        self._add_column_if_missing('articles', 'error', 'TEXT')

        # Projects
        self._add_column_if_missing('projects', 'location', 'TEXT')
        self._add_column_if_missing('projects', 'project_type', 'TEXT')
        self._add_column_if_missing('projects', 'promised_completion', 'TEXT')
        self._add_column_if_missing('projects', 'budget', 'TEXT')
        self._add_column_if_missing('projects', 'official', 'TEXT')
        self._add_column_if_missing('projects', 'status', 'TEXT')
        self._add_column_if_missing('projects', 'confidence_score', 'TEXT')

        # Project updates
        self._add_column_if_missing('project_updates', 'status', 'TEXT')
        self._add_column_if_missing('project_updates', 'source_url', 'TEXT')
        self._add_column_if_missing('project_updates', 'source_type', 'TEXT')

    def add_article(self, url: str, title: str, content: str, source: str, published_date: Optional[datetime] = None) -> Optional[int]:
        try:
            # Use raw SQL to avoid ORM selecting missing columns on older DBs
            # Check for existing URL
            try:
                row = self.session.execute(
                    sa.text('SELECT id FROM articles WHERE url = :url LIMIT 1'), {'url': url}
                ).fetchone()
            except Exception:
                row = None

            if row:
                return None

            # Build insert using only available columns
            cols = ['url', 'title', 'source', 'created_at']
            params = {'url': url, 'title': title, 'source': source, 'created_at': datetime.utcnow()}

            if 'text' in self.table_columns:
                cols.insert(2, 'text')
                params['text'] = content

            # Ensure processed flag is explicitly set (some DBs may have NULL defaults)
            if 'processed' in self.table_columns:
                cols.append('processed')
                params['processed'] = 0

            if 'published_at' in self.table_columns and published_date is not None:
                cols.append('published_at')
                params['published_at'] = published_date

            col_sql = ', '.join(cols)
            val_sql = ', '.join(':' + c for c in cols)
            insert_sql = f'INSERT INTO articles ({col_sql}) VALUES ({val_sql})'

            self.session.execute(sa.text(insert_sql), params)
            # fetch last inserted id
            last_id = self.session.execute(sa.text('SELECT last_insert_rowid()')).fetchone()[0]
            self.session.commit()
            return last_id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to add article {url}: {e}", exc_info=True)
            return None

    def get_unprocessed_articles(self, limit: int = 20) -> List[Article]:
        # If DB has mapped columns, use ORM
        if 'text' in self.table_columns and self.has_processed:
            return self.session.query(Article).filter(Article.processed == 0).order_by(Article.created_at.asc()).limit(limit).all()

        # Fallback for older DBs: select only existing columns via raw SQL and map to objects
        cols = ['id', 'title', 'url', 'source', 'published_at', 'created_at']
        available = [c for c in cols if c in self.table_columns]
        if not available:
            # If table exists but PRAGMA failed, try a minimal ORM query for ids only
            try:
                rows = self.session.execute('SELECT id FROM articles ORDER BY created_at ASC LIMIT :lim', {'lim': limit}).fetchall()
                items = []
                for r in rows:
                    items.append(SimpleNamespace(id=r[0], title=None, text='', url=None))
                return items
            except Exception:
                return []

        col_sql = ', '.join(available)
        sql = f"SELECT {col_sql} FROM articles ORDER BY created_at ASC LIMIT :lim"
        try:
            rows = self.session.execute(sql, {'lim': limit}).fetchall()
            items = []
            for r in rows:
                rowdict = {col: r[idx] for idx, col in enumerate(available)}
                ns = SimpleNamespace(
                    id=rowdict.get('id'),
                    title=rowdict.get('title'),
                    text=rowdict.get('text', ''),
                    url=rowdict.get('url'),
                )
                items.append(ns)
            return items
        except Exception:
            return []

    def mark_article_processed(self, article_id: int, error: Optional[str] = None):
        try:
            # Ensure processed column exists before attempting ORM update
            if 'processed' not in self.table_columns:
                # Try to add the column
                self._add_column_if_missing('articles', 'processed', 'INTEGER DEFAULT 0')
                # Refresh columns
                self.table_columns = set(self._get_table_columns('articles'))

            article = self.session.query(Article).get(article_id)
            if not article:
                return False
            article.processed = 1
            article.processed_at = datetime.utcnow()
            if error:
                article.error = error
            self.session.add(article)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    def find_similar_projects(self, project_name: str, location: str = "") -> List[Project]:
        # Simple similarity: name contains tokens
        q = self.session.query(Project).filter(Project.name.ilike(f"%{project_name}%"))
        results = q.limit(5).all()
        return results

    def add_project(self, project_data: Dict[str, Any]) -> Optional[int]:
        try:
            project = Project(
                name=project_data.get('project_name') or project_data.get('name'),
                description=project_data.get('description'),
                url=project_data.get('source_url'),
                location=project_data.get('location'),
                project_type=project_data.get('project_type'),
                promised_completion=project_data.get('promised_completion'),
                budget=project_data.get('budget'),
                official=project_data.get('official'),
                status=project_data.get('status'),
                confidence_score=str(project_data.get('confidence_score', project_data.get('extraction_confidence', '')))
            )
            self.session.add(project)
            self.session.commit()
            return project.id
        except Exception:
            self.session.rollback()
            return None

    def add_project_update(self, project_id: int, status: str, source_url: str, source_type: str, notes: Optional[str] = None) -> Optional[int]:
        try:
            update = ProjectUpdate(
                project_id=project_id,
                update_text=notes or "",
                status=status,
                source_url=source_url,
                source_type=source_type,
                created_at=datetime.utcnow()
            )
            self.session.add(update)
            self.session.commit()
            return update.id
        except Exception:
            self.session.rollback()
            return None

    def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        total_articles = self.session.query(func.count(Article.id)).scalar() or 0
        if self.has_processed:
            try:
                processed = self.session.query(func.count(Article.id)).filter(Article.processed == 1).scalar() or 0
            except Exception:
                processed = 0
        else:
            processed = 0

        unprocessed = total_articles - processed

        total_projects = self.session.query(func.count(Project.id)).scalar() or 0
        try:
            projects_by_status_rows = self.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
            projects_by_status = {row[0] or 'unknown': row[1] for row in projects_by_status_rows}
        except Exception:
            # Older DB schema may not have `status` column; return empty map
            projects_by_status = {}

        stats['total_articles'] = total_articles
        stats['processed_articles'] = processed
        stats['unprocessed_articles'] = unprocessed
        stats['total_projects'] = total_projects
        stats['projects_by_status'] = projects_by_status

        return stats

    def get_all_projects(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Return projects as simple objects compatible with the UI expectations.

        Each returned object has attributes used by `ui/streamlit_app.py`:
        - id, project_name, description, location, project_type, status, official, budget
        - promised_date, first_seen (datetime), last_updated (datetime), confidence_score (float)
        """
        results = []

        # Determine available columns in projects table
        project_cols = [
            'id', 'name', 'description', 'url', 'location', 'project_type',
            'promised_completion', 'budget', 'official', 'status', 'confidence_score', 'created_at'
        ]

        available = [c for c in project_cols if c in self.table_columns]

        # If ORM mapping is safe (all expected cols present), use ORM
        if set(project_cols).issubset(self.table_columns):
            projects = self.session.query(Project).all()
            for proj in projects:
                # fetch update dates
                try:
                    updates = self.session.query(ProjectUpdate).filter_by(project_id=proj.id).order_by(ProjectUpdate.update_date.asc()).all()
                except Exception:
                    updates = []

                if updates:
                    first_seen = updates[0].update_date or proj.created_at
                    last_updated = updates[-1].update_date or proj.created_at
                else:
                    first_seen = proj.created_at
                    last_updated = proj.created_at

                # parse confidence
                try:
                    confidence = float(proj.confidence_score)
                except Exception:
                    try:
                        confidence = float(str(proj.confidence_score).strip('%')) / 100.0
                    except Exception:
                        confidence = 0.0

                obj = SimpleNamespace(
                    id=proj.id,
                    project_name=proj.name,
                    description=proj.description,
                    location=proj.location,
                    project_type=proj.project_type,
                    status=proj.status,
                    official=proj.official,
                    budget=proj.budget,
                    promised_date=proj.promised_completion,
                    first_seen=first_seen,
                    last_updated=last_updated,
                    confidence_score=confidence,
                )

                results.append(obj)

            return results

        # Fallback: select only available columns via SQL and map to ui object
        if not available:
            return []

        col_sql = ', '.join(available)
        sql = f"SELECT {col_sql} FROM projects"
        try:
            rows = self.session.execute(sql).fetchall()
        except Exception:
            return []

        for r in rows:
            rowdict = {col: r[idx] for idx, col in enumerate(available)}

            # Best-effort compute first/last seen using updates table if possible
            first_seen = rowdict.get('created_at')
            last_updated = rowdict.get('created_at')
            try:
                if 'id' in rowdict and rowdict.get('id') is not None and 'update_date' in self._get_table_columns('project_updates'):
                    upd_rows = self.session.execute(
                        'SELECT update_date FROM project_updates WHERE project_id = :pid ORDER BY update_date ASC',
                        {'pid': rowdict.get('id')}
                    ).fetchall()
                    if upd_rows:
                        first_seen = upd_rows[0][0] or first_seen
                        last_updated = upd_rows[-1][0] or last_updated
            except Exception:
                pass

            # parse confidence
            confidence = 0.0
            try:
                confidence = float(rowdict.get('confidence_score'))
            except Exception:
                try:
                    confidence = float(str(rowdict.get('confidence_score', '')).strip('%')) / 100.0
                except Exception:
                    confidence = 0.0

            obj = SimpleNamespace(
                id=rowdict.get('id'),
                project_name=rowdict.get('name'),
                description=rowdict.get('description'),
                location=rowdict.get('location'),
                project_type=rowdict.get('project_type'),
                status=rowdict.get('status'),
                official=rowdict.get('official'),
                budget=rowdict.get('budget'),
                promised_date=rowdict.get('promised_completion'),
                first_seen=first_seen,
                last_updated=last_updated,
                confidence_score=confidence,
            )

            results.append(obj)

        return results

    @classmethod
    def log_scraper_run(cls, scraper_name: str, articles_collected: int, success: bool = True, duration: float = 0.0, error_message: Optional[str] = None):
        session = get_session()
        try:
            run = ScraperRun(
                scraper_name=scraper_name,
                run_timestamp=datetime.utcnow(),
                success_count=articles_collected if success else 0,
                error_count=0 if success else 1
            )
            session.add(run)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            close_session(session)

    def close(self):
        close_session(self.session)
