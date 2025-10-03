"""Tests for web application database models."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from edugain_analysis.web.models import (
    Base,
    Entity,
    Federation,
    Snapshot,
    URLValidation,
)


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_snapshot_model(db_session):
    """Test Snapshot model creation and retrieval."""
    snapshot = Snapshot(
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        total_entities=1000,
        total_sps=600,
        total_idps=400,
        sps_with_privacy=500,
        sps_missing_privacy=100,
        sps_has_security=400,
        idps_has_security=300,
        coverage_pct=83.3,
    )

    db_session.add(snapshot)
    db_session.commit()

    result = db_session.query(Snapshot).first()
    assert result is not None
    assert result.total_entities == 1000
    assert result.coverage_pct == 83.3


def test_federation_model(db_session):
    """Test Federation model with snapshot relationship."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=100,
        total_sps=60,
        total_idps=40,
        sps_with_privacy=50,
        sps_missing_privacy=10,
        sps_has_security=40,
        idps_has_security=30,
        coverage_pct=83.3,
    )
    db_session.add(snapshot)
    db_session.flush()

    federation = Federation(
        snapshot_id=snapshot.id,
        name="InCommon",
        total_entities=500,
        total_sps=300,
        total_idps=200,
        sps_with_privacy=250,
        sps_has_security=200,
        idps_has_security=150,
        coverage_pct=83.3,
    )
    db_session.add(federation)
    db_session.commit()

    result = db_session.query(Federation).first()
    assert result is not None
    assert result.name == "InCommon"
    assert result.snapshot_id == snapshot.id
    assert result.snapshot.total_entities == 100


def test_entity_model(db_session):
    """Test Entity model with relationships."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=10,
        total_sps=6,
        total_idps=4,
        sps_with_privacy=5,
        sps_missing_privacy=1,
        sps_has_security=4,
        idps_has_security=3,
        coverage_pct=83.3,
    )
    db_session.add(snapshot)
    db_session.flush()

    federation = Federation(
        snapshot_id=snapshot.id,
        name="TestFederation",
        total_entities=50,
        total_sps=30,
        total_idps=20,
        sps_with_privacy=25,
        sps_has_security=20,
        idps_has_security=15,
        coverage_pct=83.3,
    )
    db_session.add(federation)
    db_session.flush()

    entity = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://sp.example.org/shibboleth",
        entity_type="SP",
        organization_name="Example University",
        has_privacy_statement=True,
        privacy_statement_url="https://example.org/privacy",
        has_security_contact=True,
    )
    db_session.add(entity)
    db_session.commit()

    result = db_session.query(Entity).first()
    assert result is not None
    assert result.entity_id == "https://sp.example.org/shibboleth"
    assert result.entity_type == "SP"
    assert result.has_privacy_statement is True
    assert result.federation.name == "TestFederation"
    assert result.snapshot.total_entities == 10


def test_url_validation_model(db_session):
    """Test URLValidation model with entity relationship."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=10,
        total_sps=6,
        total_idps=4,
        sps_with_privacy=5,
        sps_missing_privacy=1,
        sps_has_security=4,
        idps_has_security=3,
        coverage_pct=83.3,
    )
    db_session.add(snapshot)
    db_session.flush()

    federation = Federation(
        snapshot_id=snapshot.id,
        name="TestFed",
        total_entities=50,
        total_sps=30,
        total_idps=20,
        sps_with_privacy=25,
        sps_has_security=20,
        idps_has_security=15,
        coverage_pct=83.3,
    )
    db_session.add(federation)
    db_session.flush()

    entity = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://sp.test.org/shibboleth",
        entity_type="SP",
        organization_name="Test Org",
        has_privacy_statement=True,
        privacy_statement_url="https://test.org/privacy",
        has_security_contact=False,
    )
    db_session.add(entity)
    db_session.flush()

    validation = URLValidation(
        entity_id=entity.id,
        url="https://test.org/privacy",
        status_code=200,
        final_url="https://test.org/privacy",
        accessible=True,
        redirect_count=0,
        validation_error=None,
        validated_at=datetime.now(),
    )
    db_session.add(validation)
    db_session.commit()

    result = db_session.query(URLValidation).first()
    assert result is not None
    assert result.status_code == 200
    assert result.accessible is True
    assert result.entity.organization_name == "Test Org"


def test_cascade_delete(db_session):
    """Test cascade delete relationships."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=10,
        total_sps=6,
        total_idps=4,
        sps_with_privacy=5,
        sps_missing_privacy=1,
        sps_has_security=4,
        idps_has_security=3,
        coverage_pct=83.3,
    )
    db_session.add(snapshot)
    db_session.flush()

    federation = Federation(
        snapshot_id=snapshot.id,
        name="TestFed",
        total_entities=50,
        total_sps=30,
        total_idps=20,
        sps_with_privacy=25,
        sps_has_security=20,
        idps_has_security=15,
        coverage_pct=83.3,
    )
    db_session.add(federation)
    db_session.flush()

    entity = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://sp.test.org/shibboleth",
        entity_type="SP",
        organization_name="Test Org",
        has_privacy_statement=True,
        privacy_statement_url="https://test.org/privacy",
        has_security_contact=False,
    )
    db_session.add(entity)
    db_session.commit()

    # Delete snapshot should cascade to federation and entity
    db_session.delete(snapshot)
    db_session.commit()

    assert db_session.query(Snapshot).count() == 0
    assert db_session.query(Federation).count() == 0
    assert db_session.query(Entity).count() == 0


def test_entity_filtering(db_session):
    """Test filtering entities by type and status."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=20,
        total_sps=12,
        total_idps=8,
        sps_with_privacy=10,
        sps_missing_privacy=2,
        sps_has_security=8,
        idps_has_security=6,
        coverage_pct=83.3,
    )
    db_session.add(snapshot)
    db_session.flush()

    federation = Federation(
        snapshot_id=snapshot.id,
        name="TestFed",
        total_entities=100,
        total_sps=60,
        total_idps=40,
        sps_with_privacy=50,
        sps_has_security=40,
        idps_has_security=30,
        coverage_pct=83.3,
    )
    db_session.add(federation)
    db_session.flush()

    # Add SPs with different statuses
    sp1 = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://sp1.test.org",
        entity_type="SP",
        has_privacy_statement=True,
        has_security_contact=True,
    )
    sp2 = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://sp2.test.org",
        entity_type="SP",
        has_privacy_statement=False,
        has_security_contact=True,
    )

    # Add IdP
    idp1 = Entity(
        snapshot_id=snapshot.id,
        federation_id=federation.id,
        entity_id="https://idp1.test.org",
        entity_type="IdP",
        has_privacy_statement=False,
        has_security_contact=True,
    )

    db_session.add_all([sp1, sp2, idp1])
    db_session.commit()

    # Test filtering by entity type
    sps = db_session.query(Entity).filter(Entity.entity_type == "SP").all()
    assert len(sps) == 2

    idps = db_session.query(Entity).filter(Entity.entity_type == "IdP").all()
    assert len(idps) == 1

    # Test filtering by privacy statement
    with_privacy = db_session.query(Entity).filter(Entity.has_privacy_statement).all()
    assert len(with_privacy) == 1

    # Test filtering by security status
    with_security = db_session.query(Entity).filter(Entity.has_security_contact).all()
    assert len(with_security) == 3
