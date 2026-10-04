"""Phase 5: one response shape for every endpoint — success and error alike."""

from tests.fakes import auth_headers, install_fake_db


def test_success_envelope_has_data_request_id_timestamp(client):
    res = client.get("/api/v1/health")
    body = res.json()
    assert set(body) == {"data", "request_id", "timestamp"}
    assert len(body["request_id"]) == 32
    assert "T" in body["timestamp"]  # ISO-8601


def test_404_uses_error_envelope(client):
    res = client.get("/api/v1/does-not-exist")
    assert res.status_code == 404
    body = res.json()
    assert set(body) == {"error", "request_id", "timestamp"}
    assert body["error"]["code"] == 404
    assert body["error"]["message"]


def test_401_uses_error_envelope(client):
    res = client.get("/api/v1/me/profile")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == 401


def test_422_includes_field_level_details(client, monkeypatch):
    install_fake_db(monkeypatch)
    res = client.get("/api/v1/matches?limit=999", headers=auth_headers("alice"))
    assert res.status_code == 422
    error = res.json()["error"]
    assert error["code"] == 422
    assert any("limit" in detail["field"] for detail in error["details"])


def test_openapi_is_not_wrapped(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    assert "paths" in res.json()  # raw schema, no envelope


def test_timestamps_differ_between_requests(client):
    first = client.get("/api/v1/health").json()["timestamp"]
    second = client.get("/api/v1/health").json()["timestamp"]
    assert first != second, "timestamps must be computed per response, not at import"
