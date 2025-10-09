"""Database models for web application."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

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
    sps_has_sirtfi = Column(Integer, default=0)
    idps_has_sirtfi = Column(Integer, default=0)
    total_has_sirtfi = Column(Integer, default=0)
    coverage_pct = Column(Float)

    # Cache metadata
    metadata_source = Column(
        String(500), default="eduGAIN Production"
    )  # Source of metadata
    cache_age_hours = Column(Float)  # Age of metadata cache in hours

    # Relationships
    federations = relationship(
        "Federation", back_populates="snapshot", cascade="all, delete-orphan"
    )
    entities = relationship(
        "Entity", back_populates="snapshot", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_timestamp_desc", timestamp.desc()),)


class Federation(Base):
    """Federation statistics per snapshot."""

    __tablename__ = "federations"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), index=True)
    name = Column(String(200), index=True)
    total_entities = Column(Integer)
    total_sps = Column(Integer)
    total_idps = Column(Integer)
    sps_with_privacy = Column(Integer)
    sps_has_security = Column(Integer)
    idps_has_security = Column(Integer)
    sps_has_sirtfi = Column(Integer, default=0)
    idps_has_sirtfi = Column(Integer, default=0)
    total_has_sirtfi = Column(Integer, default=0)
    coverage_pct = Column(Float)

    # Relationships
    snapshot = relationship("Snapshot", back_populates="federations")
    entities = relationship(
        "Entity", back_populates="federation", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_snapshot_federation", snapshot_id, name),)


class Entity(Base):
    """Individual entity (SP or IdP) for detailed tracking."""

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), index=True)
    federation_id = Column(Integer, ForeignKey("federations.id"), index=True)
    entity_id = Column(
        String(500), nullable=False, index=True
    )  # SAML EntityID (can be long URL)
    entity_type = Column(String(10), nullable=False, index=True)  # "SP" or "IdP"
    organization_name = Column(String(500))
    has_privacy_statement = Column(Boolean, default=False)
    privacy_statement_url = Column(Text)  # Can be very long URL
    has_security_contact = Column(Boolean, default=False)
    has_sirtfi = Column(Boolean, default=False)

    # Relationships
    snapshot = relationship("Snapshot", back_populates="entities")
    federation = relationship("Federation", back_populates="entities")
    url_validations = relationship(
        "URLValidation", back_populates="entity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_entity_snapshot", snapshot_id, entity_id),
        Index("idx_entity_federation_type", federation_id, entity_type),
        Index("idx_entity_privacy_status", has_privacy_statement),
        Index("idx_entity_security_status", has_security_contact),
        Index("idx_entity_sirtfi_status", has_sirtfi),
    )


class URLValidation(Base):
    """URL validation results for privacy statement URLs."""

    __tablename__ = "url_validations"

    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    url = Column(Text, nullable=False)
    status_code = Column(Integer)  # HTTP status code (200, 404, etc.)
    final_url = Column(Text)  # URL after redirects
    accessible = Column(Boolean, default=False)
    redirect_count = Column(Integer, default=0)
    validation_error = Column(Text)  # Error message if validation failed
    validated_at = Column(DateTime, default=datetime.now, index=True)

    # Relationship
    entity = relationship("Entity", back_populates="url_validations")

    __table_args__ = (
        Index("idx_validation_entity_url", entity_id, url),
        Index("idx_validation_status", status_code, accessible),
    )


class Settings(Base):
    """Application settings (singleton table)."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    auto_refresh_interval = Column(Integer, default=12)  # Hours
    url_validation_timeout = Column(Integer, default=10)  # Seconds
    url_validation_threads = Column(Integer, default=10)  # Thread pool size
    metadata_cache_expiry = Column(Integer, default=12)  # Hours
    federation_cache_expiry = Column(Integer, default=720)  # Hours (30 days)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def get_database_file_path() -> Path:
    """Get XDG-compliant database file path as Path object."""
    try:
        from platformdirs import user_cache_dir

        cache_dir = Path(user_cache_dir("edugain-analysis", "edugain"))
    except ImportError:
        cache_dir = Path.home() / ".cache" / "edugain-analysis"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "webapp.db"


def get_database_path() -> str:
    """Get XDG-compliant database path as SQLite URL."""
    return f"sqlite:///{get_database_file_path()}"


def create_database():
    """Create database with optimizations."""
    database_url = get_database_path()

    engine = create_engine(
        database_url,
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
