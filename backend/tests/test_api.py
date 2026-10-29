import hashlib
import hmac
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_and_login():
    response = client.post("/api/v1/auth/register", json={"email": "dev@example.com", "password": "a-very-strong-password"})
    assert response.status_code == 201
    response = client.post("/api/v1/auth/login", data={"username": "dev@example.com", "password": "a-very-strong-password"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_live():
    assert client.get("/health/live").json()["status"] == "ok"


def test_register_login_and_me():
    token = register_and_login()
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "dev@example.com"


def test_duplicate_registration_rejected():
    register_and_login()
    response = client.post("/api/v1/auth/register", json={"email": "dev@example.com", "password": "another-strong-password"})
    assert response.status_code == 409


def test_review_requires_auth():
    response = client.post("/api/v1/reviews", json={"language": "python", "code": "print('hello')"})
    assert response.status_code == 401


def test_review_and_history():
    token = register_and_login()
    response = client.post("/api/v1/reviews", headers={"Authorization": f"Bearer {token}"},
                           json={"language": "python", "code": "import os\nprint('hello')"})
    assert response.status_code == 201
    assert "findings" in response.json()
    history = client.get("/api/v1/reviews", headers={"Authorization": f"Bearer {token}"})
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_github_webhook_signature():
    body = b'{"action":"opened"}'
    signature = "sha256=" + hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()
    response = client.post("/api/v1/github/webhook", content=body, headers={
        "X-Hub-Signature-256": signature, "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    })
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_bad_github_signature_rejected():
    response = client.post("/api/v1/github/webhook", content=b"{}", headers={
        "X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "push"
    })
    assert response.status_code == 401
