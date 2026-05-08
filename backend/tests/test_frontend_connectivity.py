import os

from fastapi.testclient import TestClient

os.environ.setdefault("FRONTEND_URL", "https://frontend.example.com")

from app.main import create_app


client = TestClient(create_app())


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_frontend_origin():
    response = client.get(
        "/health",
        headers={"Origin": "https://frontend.example.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://frontend.example.com"