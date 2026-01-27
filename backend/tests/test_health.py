"""Tests for health check endpoints."""


def test_root_endpoint(client):
    """Test the root endpoint returns service info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ResMatch API"
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "gemini" in data
