import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DB", str(tmp_path / "test.db"))
    import importlib

    import app.main as main
    importlib.reload(main)
    return TestClient(main.app)


def test_register_and_login(client):
    assert client.post("/users", json={"email": "a@example.org", "password": "pw-123456"}).status_code == 201
    r = client.post("/login", json={"email": "a@example.org", "password": "pw-123456"})
    assert r.status_code == 200 and r.json()["token"]


def test_wrong_password_is_rejected(client):
    client.post("/users", json={"email": "b@example.org", "password": "pw-123456"})
    assert client.post("/login", json={"email": "b@example.org", "password": "nope"}).status_code == 401


def test_duplicate_email(client):
    body = {"email": "c@example.org", "password": "pw-123456"}
    client.post("/users", json=body)
    assert client.post("/users", json=body).status_code == 409
