import pytest

pytestmark = pytest.mark.django_db(transaction=True)


def test_register_login_me(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "supersecret1",
            "display_name": "Alice",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["email"] == "alice@example.com"

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "supersecret1"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()

    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_login_wrong_password(client, user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_duplicate_email(client, user):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "username": "someone", "password": "supersecret1"},
    )
    assert resp.status_code == 409


def test_refresh(client, user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "s3cretpass"},
    )
    refresh_token = resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
