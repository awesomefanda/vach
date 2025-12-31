"""
Database models and initialization for Vach
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from pathlib import Path
from config.settings import DATABASE_PATH
from config.logging_config import get_logger

logger = get_logger(__name__)

Base = declarative_base()

# --- TABLE MODELS --- #
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    text = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime)
    processed = Column(Integer, default=0)
    processed_at = Column(DateTime)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    url = Column(String(500))
    location = Column(String(200))
    project_type = Column(String(50))
    promised_completion = Column(String(50))
    budget = Column(String(100))
    official = Column(String(200))
    status = Column(String(50))
    confidence_score = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

    updates = relationship("ProjectUpdate", back_populates="project", cascade="all, delete")


class ProjectUpdate(Base):
    __tablename__ = "project_updates"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    update_text = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    update_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))
    source_url = Column(String(500))
    source_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="updates")


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(Integer, primary_key=True)
    scraper_name = Column(String(100), nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)


# --- ENGINE & SESSION MANAGEMENT --- #
db_path = Path(DATABASE_PATH)
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()


def close_session(session):
    session.close()


# --- DATABASE CREATION FUNCTION --- #
def init_database():
    """Create all tables if they do not exist"""
    try:
        logger.info(f"Creating database at {DATABASE_PATH}")
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False
