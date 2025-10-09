"""Unit tests for web application routes and endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from edugain_analysis.web.app import app, get_db
from edugain_analysis.web.models import (
    Base,
    Entity,
    Federation,
    Snapshot,
    URLValidation,
)


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    """Create test client with test database."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_snapshot(test_db):
    """Create a sample snapshot with data."""
    snapshot = Snapshot(
        timestamp=datetime.now(),
        total_entities=100,
        total_sps=60,
        total_idps=40,
        sps_with_privacy=45,
        sps_missing_privacy=15,
        sps_has_security=30,
        idps_has_security=25,
        coverage_pct=75.0,
        metadata_source="eduGAIN Production",
        cache_age_hours=2.5,
    )
    test_db.add(snapshot)
    test_db.commit()
    test_db.refresh(snapshot)

    # Add federations
    fed1 = Federation(
        snapshot_id=snapshot.id,
        name="InCommon",
        total_entities=50,
        total_sps=30,
        total_idps=20,
        sps_with_privacy=25,
        sps_has_security=20,
        idps_has_security=15,
        coverage_pct=83.33,
    )
    fed2 = Federation(
        snapshot_id=snapshot.id,
        name="DFN-AAI",
        total_entities=30,
        total_sps=20,
        total_idps=10,
        sps_with_privacy=15,
        sps_has_security=10,
        idps_has_security=8,
        coverage_pct=75.0,
    )
    test_db.add_all([fed1, fed2])
    test_db.commit()

    # Add entities
    entity1 = Entity(
        snapshot_id=snapshot.id,
        federation_id=fed1.id,
        entity_id="https://example.org/sp1",
        entity_type="SP",
        organization_name="Example University",
        has_privacy_statement=True,
        privacy_statement_url="https://example.org/privacy",
        has_security_contact=True,
    )
    entity2 = Entity(
        snapshot_id=snapshot.id,
        federation_id=fed1.id,
        entity_id="https://example.org/idp1",
        entity_type="IdP",
        organization_name="Example College",
        has_privacy_statement=False,
        privacy_statement_url=None,
        has_security_contact=False,
    )
    test_db.add_all([entity1, entity2])
    test_db.commit()

    # Add URL validation
    url_val = URLValidation(
        entity_id=entity1.entity_id,
        url="https://example.org/privacy",
        status_code=200,
        final_url="https://example.org/privacy",
        accessible=True,
        redirect_count=0,
        validation_error=None,
        validated_at=datetime.now(),
    )
    test_db.add(url_val)
    test_db.commit()

    return snapshot


class TestMainRoutes:
    """Test main page routes."""

    def test_dashboard_empty(self, client):
        """Test dashboard with no data."""
        response = client.get("/")
        assert response.status_code == 200
        assert (
            b"No data available" in response.content
            or b"empty" in response.content.lower()
        )

    def test_dashboard_with_data(self, client, sample_snapshot):
        """Test dashboard with sample data."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Dashboard" in response.content or b"eduGAIN" in response.content
        assert b"100" in response.content  # Total entities

    def test_federations_page(self, client, sample_snapshot):
        """Test federations list page."""
        response = client.get("/federations")
        assert response.status_code == 200
        assert b"InCommon" in response.content
        assert b"DFN-AAI" in response.content

    def test_federation_detail(self, client, sample_snapshot):
        """Test federation detail page."""
        response = client.get("/federations/InCommon")
        assert response.status_code == 200
        assert b"InCommon" in response.content
        assert b"50" in response.content  # Total entities

    def test_federation_detail_not_found(self, client, sample_snapshot):
        """Test federation detail page with non-existent federation."""
        response = client.get("/federations/NonExistent")
        assert response.status_code == 200
        assert (
            b"not found" in response.content.lower()
            or b"Federation Not Found" in response.content
        )

    def test_entity_detail(self, client, sample_snapshot):
        """Test entity detail page."""
        response = client.get("/entities/https://example.org/sp1")
        assert response.status_code == 200
        assert (
            b"Example University" in response.content
            or b"https://example.org/sp1" in response.content
        )

    def test_entity_detail_not_found(self, client, sample_snapshot):
        """Test entity detail page with non-existent entity."""
        response = client.get("/entities/https://nonexistent.org/entity")
        assert response.status_code == 200
        assert (
            b"not found" in response.content.lower()
            or b"Entity not found" in response.content
        )

    def test_validation_page(self, client, sample_snapshot):
        """Test URL validation page."""
        response = client.get("/validation")
        assert response.status_code == 200
        assert b"validation" in response.content.lower() or b"URL" in response.content

    def test_config_page(self, client, sample_snapshot):
        """Test configuration page."""
        response = client.get("/config")
        assert response.status_code == 200
        assert (
            b"config" in response.content.lower()
            or b"settings" in response.content.lower()
        )

    def test_history_page(self, client, sample_snapshot):
        """Test history page."""
        response = client.get("/history")
        assert response.status_code == 200
        assert (
            b"historical" in response.content.lower()
            or b"history" in response.content.lower()
        )

    def test_history_page_with_params(self, client, sample_snapshot):
        """Test history page with query parameters."""
        response = client.get("/history?days=7&federation_name=InCommon")
        assert response.status_code == 200


class TestHTMXPartials:
    """Test HTMX partial routes."""

    def test_stats_partial(self, client, sample_snapshot):
        """Test stats cards partial."""
        response = client.get("/partials/stats")
        assert response.status_code == 200
        assert b"100" in response.content  # Total entities

    def test_stats_partial_empty(self, client):
        """Test stats partial with no data."""
        response = client.get("/partials/stats")
        assert response.status_code == 200

    def test_federations_partial(self, client, sample_snapshot):
        """Test federations table partial."""
        response = client.get("/partials/federations")
        assert response.status_code == 200
        assert b"InCommon" in response.content

    def test_federations_partial_with_sorting(self, client, sample_snapshot):
        """Test federations partial with sorting."""
        response = client.get("/partials/federations?sort=coverage&order=desc")
        assert response.status_code == 200

    def test_entity_table_partial(self, client, sample_snapshot):
        """Test entity table partial."""
        response = client.get("/partials/entity_table?federation_id=1")
        assert response.status_code == 200

    def test_entity_table_partial_with_filters(self, client, sample_snapshot):
        """Test entity table partial with filters."""
        response = client.get(
            "/partials/entity_table?entity_type=SP&privacy_filter=yes&security_filter=yes"
        )
        assert response.status_code == 200

    def test_entity_changes_partial(self, client, test_db, sample_snapshot):
        """Test entity changes partial."""
        # Create second snapshot for comparison
        snapshot2 = Snapshot(
            timestamp=datetime.now() + timedelta(days=1),
            total_entities=105,
            total_sps=62,
            total_idps=43,
            sps_with_privacy=47,
            sps_missing_privacy=15,
            sps_has_security=32,
            idps_has_security=27,
            coverage_pct=76.0,
        )
        test_db.add(snapshot2)
        test_db.commit()
        test_db.refresh(snapshot2)

        response = client.get(f"/partials/entity_changes?snapshot1_id={snapshot2.id}")
        assert response.status_code == 200

    def test_search_partial(self, client, sample_snapshot):
        """Test search partial."""
        response = client.get("/partials/search?q=Example")
        assert response.status_code == 200
        assert b"Example University" in response.content


class TestAPIEndpoints:
    """Test JSON API endpoints."""

    def test_api_snapshot_latest(self, client, sample_snapshot):
        """Test latest snapshot API."""
        response = client.get("/api/snapshot/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["total_entities"] == 100
        assert data["coverage_pct"] == 75.0

    def test_api_snapshot_latest_empty(self, client):
        """Test latest snapshot API with no data."""
        response = client.get("/api/snapshot/latest")
        assert response.status_code == 200
        data = response.json()
        assert data == {"error": "No data available"}

    def test_api_federations(self, client, sample_snapshot):
        """Test federations API."""
        response = client.get("/api/federations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["InCommon", "DFN-AAI"]

    def test_api_search(self, client, sample_snapshot):
        """Test search API."""
        response = client.get("/api/search?q=Example")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) > 0
        assert data["entities"][0]["organization_name"] == "Example University"

    def test_api_search_empty_query(self, client, sample_snapshot):
        """Test search API with empty query."""
        response = client.get("/api/search?q=")
        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == []
        assert data["federations"] == []

    def test_api_cache_status(self, client, sample_snapshot):
        """Test cache status API."""
        response = client.get("/api/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "cache_age_hours" in data
        assert "status" in data
        assert data["cache_age_hours"] == 2.5

    def test_api_settings_get(self, client):
        """Test get settings API."""
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "auto_refresh_interval" in data

    def test_api_settings_post(self, client):
        """Test update settings API."""
        response = client.post(
            "/api/settings?auto_refresh_interval=30&url_validation_timeout=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["settings"]["auto_refresh_interval"] == 30

    def test_api_settings_reset(self, client):
        """Test reset settings API."""
        response = client.post("/api/settings/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Settings reset to defaults"

    def test_api_export_entities_csv(self, client, sample_snapshot):
        """Test entity CSV export API."""
        response = client.get("/api/export/entities?export_format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert b"Example University" in response.content

    def test_api_export_entities_json(self, client, sample_snapshot):
        """Test entity JSON export API."""
        response = client.get("/api/export/entities?export_format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert data["total_entities"] == 2  # 2 entities in sample data
        assert len(data["entities"]) == 2

    def test_api_export_entities_with_filters(self, client, sample_snapshot):
        """Test entity export with filters."""
        response = client.get(
            "/api/export/entities?export_format=json&entity_type=SP&privacy_filter=yes"
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert all(e["entity_type"] == "SP" for e in entities)
        assert all(e["has_privacy_statement"] for e in entities)

    def test_api_export_federations_csv(self, client, sample_snapshot):
        """Test federation CSV export API."""
        response = client.get("/api/export/federations?export_format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert b"InCommon" in response.content

    def test_api_export_federations_json(self, client, sample_snapshot):
        """Test federation JSON export API."""
        response = client.get("/api/export/federations?export_format=json")
        assert response.status_code == 200
        data = response.json()
        assert data["total_federations"] == 2
        assert len(data["federations"]) == 2

    def test_api_refresh_status_idle(self, client):
        """Test refresh status when idle."""
        response = client.get("/api/refresh/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "status" in data

    def test_api_settings_validation_invalid_range(self, client):
        """Test settings validation with values outside allowed ranges."""
        # Test invalid auto_refresh_interval (too high)
        response = client.post("/api/settings?auto_refresh_interval=200")
        assert response.status_code == 200
        data = response.json()
        # Should return error or ignore invalid value
        if "error" not in data:
            # If no error, value should be clamped or unchanged
            settings = client.get("/api/settings").json()
            assert settings["auto_refresh_interval"] <= 168

    def test_api_cache_status_no_snapshot(self, client):
        """Test cache status when no snapshot exists."""
        response = client.get("/api/cache/status")
        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully when no snapshot
        assert "status" in data or "error" in data


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_route(self, client):
        """Test accessing invalid route."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_malformed_query_params(self, client, sample_snapshot):
        """Test with malformed query parameters."""
        response = client.get("/history?days=invalid")
        # FastAPI validation may return 422 for invalid types
        assert response.status_code in [200, 400, 422]

    def test_very_long_entity_id(self, client, sample_snapshot):
        """Test with very long entity ID."""
        long_id = "https://example.org/" + "a" * 1000
        response = client.get(f"/entities/{long_id}")
        assert response.status_code == 200
        assert (
            b"not found" in response.content.lower() or b"No data" in response.content
        )

    def test_special_characters_in_search(self, client, sample_snapshot):
        """Test search with special characters."""
        response = client.get("/api/search?q=%20%3C%3E%22%27")
        assert response.status_code == 200

    def test_concurrent_database_access(self, client, sample_snapshot):
        """Test multiple concurrent requests."""
        responses = []
        for _ in range(5):
            responses.append(client.get("/"))

        assert all(r.status_code == 200 for r in responses)

    def test_empty_state_all_routes(self, client):
        """Test all main routes with no data (empty state)."""
        # Dashboard
        response = client.get("/")
        assert response.status_code == 200

        # Federations
        response = client.get("/federations")
        assert response.status_code == 200

        # Validation
        response = client.get("/validation")
        assert response.status_code == 200

        # History
        response = client.get("/history")
        assert response.status_code == 200

        # Config
        response = client.get("/config")
        assert response.status_code == 200

    def test_large_result_set(self, client, test_db):
        """Test with large number of entities."""
        snapshot = Snapshot(
            timestamp=datetime.now(),
            total_entities=1000,
            total_sps=600,
            total_idps=400,
            sps_with_privacy=450,
            sps_missing_privacy=150,
            sps_has_security=300,
            idps_has_security=250,
            coverage_pct=75.0,
        )
        test_db.add(snapshot)
        test_db.commit()

        fed = Federation(
            snapshot_id=snapshot.id,
            name="Large Federation",
            total_entities=1000,
            total_sps=600,
            total_idps=400,
            sps_with_privacy=450,
            sps_has_security=300,
            idps_has_security=250,
            coverage_pct=75.0,
        )
        test_db.add(fed)
        test_db.commit()

        # Add many entities
        entities = [
            Entity(
                snapshot_id=snapshot.id,
                federation_id=fed.id,
                entity_id=f"https://example.org/entity{i}",
                entity_type="SP" if i % 2 == 0 else "IdP",
                organization_name=f"Organization {i}",
                has_privacy_statement=i % 3 == 0,
                privacy_statement_url=f"https://example.org/privacy{i}"
                if i % 3 == 0
                else None,
                has_security_contact=i % 4 == 0,
            )
            for i in range(100)
        ]
        test_db.add_all(entities)
        test_db.commit()

        response = client.get("/federations/Large%20Federation")
        assert response.status_code == 200
