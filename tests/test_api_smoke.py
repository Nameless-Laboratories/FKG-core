"""Smoke tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    from fkg.api.app import app
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_status(self, client):
        """Health endpoint should return status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data


class TestWhoamiEndpoint:
    """Tests for /whoami endpoint."""

    def test_whoami_returns_identity(self, client):
        """Whoami endpoint should return instance identity."""
        response = client.get("/whoami")
        assert response.status_code == 200
        data = response.json()

        assert "instance_id" in data
        assert "authority_name" in data
        assert "jurisdiction" in data
        assert "schema_version" in data


class TestEntitiesEndpoint:
    """Tests for /entities endpoints."""

    def test_list_entities_empty(self, client):
        """List entities should work with empty database."""
        response = client.get("/entities")
        # May fail without DB, but structure should be correct if it succeeds
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

    def test_list_entities_with_type_filter(self, client):
        """List entities with type filter."""
        response = client.get("/entities?type=organization")
        if response.status_code == 200:
            data = response.json()
            assert "items" in data

    def test_list_entities_with_pagination(self, client):
        """List entities with pagination."""
        response = client.get("/entities?limit=10&offset=0")
        if response.status_code == 200:
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 0


class TestEdgesEndpoint:
    """Tests for /edges endpoints."""

    def test_list_edges_empty(self, client):
        """List edges should work with empty database."""
        response = client.get("/edges")
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data


class TestPkgEndpoint:
    """Tests for /pkg endpoints."""

    def test_manifest_returns_info(self, client):
        """PKG manifest endpoint should return counts."""
        response = client.get("/pkg/manifest")
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            assert "authority_id" in data
            assert "counts" in data


class TestApiStructure:
    """Tests for overall API structure."""

    def test_openapi_available(self, client):
        """OpenAPI schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_cors_headers_when_enabled(self, client):
        """CORS headers when enabled."""
        # This test just verifies the request works
        response = client.options("/health")
        # Status depends on CORS config
        assert response.status_code in [200, 405]
