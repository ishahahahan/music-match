"""Boot + contract smoke: the app imports, serves /api/v1/health, and documents itself."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_returns_ok():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "musicmatch-api"}


def test_openapi_documents_v1_routes():
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/matches" in paths


def test_unimplemented_phase_returns_501():
    assert client.get("/api/v1/me/profile").status_code == 501
