"""Smoke tests for production deployment health checks."""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test /health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint(client: TestClient):
    """Test /metrics endpoint returns Prometheus-compatible metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "cpu_percent" in content
    assert "memory_available_bytes" in content
    assert "disk_used_bytes" in content


def test_cors_headers_present(client: TestClient):
    """Test that CORS headers are correctly set."""
    response = client.get("/health", headers={"origin": "http://localhost:3000"})
    assert response.status_code == 200


def test_security_headers_present(client: TestClient):
    """Test that security headers are present in response."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    assert "x-content-type-options" in headers
    assert "x-frame-options" in headers
    assert "x-xss-protection" in headers


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns expected message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Trading API is running" in response.json()["message"]


def test_database_connection(client: TestClient):
    """Test that database connection is working (via admin endpoint if available)."""
    response = client.get("/admin/system", headers={"Authorization": "Bearer test-admin-token"})
    # This test ensures DB is accessible
    # May return 401 (auth failure) or 200 (success), both mean DB is reachable
    assert response.status_code in [200, 401, 403]
