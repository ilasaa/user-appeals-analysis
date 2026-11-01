"""HTTP smoke tests that do not need PostgreSQL."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Appeals Analysis API is running"
    }


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_appeal_invalid_title():
    response = client.post(
        "/api/appeals",
        json={"title": "Hi", "description": "Не могу войти в аккаунт"},
    )
    assert response.status_code == 422
