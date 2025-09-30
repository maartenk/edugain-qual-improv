"""Database models for web application."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Snapshot(Base):
    """Analysis snapshot for historical tracking."""

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    total_entities = Column(Integer)
    total_sps = Column(Integer)
    total_idps = Column(Integer)
    sps_with_privacy = Column(Integer)
    sps_missing_privacy = Column(Integer)
    sps_has_security = Column(Integer)
    idps_has_security = Column(Integer)
    coverage_pct = Column(Float)

    __table_args__ = (Index("idx_timestamp_desc", timestamp.desc()),)


class Federation(Base):
    """Federation statistics per snapshot."""

    __tablename__ = "federations"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, index=True)
    name = Column(String(200), index=True)
    total_entities = Column(Integer)
    total_sps = Column(Integer)
    total_idps = Column(Integer)
    sps_with_privacy = Column(Integer)
    sps_has_security = Column(Integer)
    idps_has_security = Column(Integer)
    coverage_pct = Column(Float)

    __table_args__ = (Index("idx_snapshot_federation", snapshot_id, name),)


def get_database_path() -> str:
    """Get XDG-compliant database path."""
    try:
        from platformdirs import user_cache_dir

        cache_dir = Path(user_cache_dir("edugain-analysis", "edugain"))
    except ImportError:
        cache_dir = Path.home() / ".cache" / "edugain-analysis"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{cache_dir / 'webapp.db'}"


def create_database():
    """Create database with optimizations."""
    DATABASE_URL = get_database_path()

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
        echo=False,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    return engine


# Create session factory
engine = create_database()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
