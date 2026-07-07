import pytest
from django.contrib.auth.hashers import make_password

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def second_user(db):
    from apps.accounts.models import User

    return User.objects.create(
        email="bob@example.com",
        username="bob",
        password=make_password("s3cretpass"),
        display_name="Bob",
    )


@pytest.fixture
def second_auth_headers(second_user):
    from api.security import create_token

    return {"Authorization": f"Bearer {create_token(second_user.id)}"}


@pytest.fixture
def poi(client, auth_headers):
    resp = client.post(
        "/api/v1/pois",
        json={"title": "Vondelpark", "location": {"lat": 52.3579, "lng": 4.8686}},
        headers=auth_headers,
    )
    return resp.json()


# --- Follow ------------------------------------------------------------------


def test_follow_unfollow(client, user, second_user, auth_headers):
    assert client.post("/api/v1/users/bob/follow", headers=auth_headers).status_code == 204
    # Idempotent
    assert client.post("/api/v1/users/bob/follow", headers=auth_headers).status_code == 204

    profile = client.get("/api/v1/users/bob", headers=auth_headers).json()
    assert profile["followers_count"] == 1
    assert profile["is_following"] is True
    assert "email" not in profile  # public profile must not leak email

    followers = client.get("/api/v1/users/bob/followers").json()
    assert [f["username"] for f in followers] == ["tester"]

    assert client.delete("/api/v1/users/bob/follow", headers=auth_headers).status_code == 204
    assert client.get("/api/v1/users/bob").json()["followers_count"] == 0


def test_cannot_follow_self(client, user, auth_headers):
    resp = client.post("/api/v1/users/tester/follow", headers=auth_headers)
    assert resp.status_code == 422


def test_follow_requires_auth(client, second_user):
    assert client.post("/api/v1/users/bob/follow").status_code == 401


# --- Check-ins ---------------------------------------------------------------


def test_checkin_increments_visit_count(client, poi, auth_headers):
    resp = client.post(
        f"/api/v1/pois/{poi['id']}/checkin",
        json={"comment": "Lovely morning run"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["comment"] == "Lovely morning run"

    updated = client.get(f"/api/v1/pois/{poi['id']}").json()
    assert updated["visit_count"] == 1


# --- Reviews -----------------------------------------------------------------


def test_review_updates_rating(client, poi, auth_headers, second_auth_headers):
    resp = client.post(
        f"/api/v1/pois/{poi['id']}/reviews",
        json={"rating": 5, "text": "Perfect"},
        headers=auth_headers,
    )
    assert resp.status_code == 201

    client.post(
        f"/api/v1/pois/{poi['id']}/reviews",
        json={"rating": 3, "text": "Crowded"},
        headers=second_auth_headers,
    )

    updated = client.get(f"/api/v1/pois/{poi['id']}").json()
    assert updated["rating_count"] == 2
    assert updated["rating_avg"] == 4.0

    reviews = client.get(f"/api/v1/pois/{poi['id']}/reviews").json()
    assert len(reviews) == 2


def test_review_upsert_not_duplicate(client, poi, auth_headers):
    client.post(
        f"/api/v1/pois/{poi['id']}/reviews", json={"rating": 2}, headers=auth_headers
    )
    client.post(
        f"/api/v1/pois/{poi['id']}/reviews", json={"rating": 4}, headers=auth_headers
    )
    updated = client.get(f"/api/v1/pois/{poi['id']}").json()
    assert updated["rating_count"] == 1
    assert updated["rating_avg"] == 4.0


# --- Saved routes ------------------------------------------------------------


def test_save_route(client, auth_headers, second_auth_headers, poi):
    resp = client.post(
        "/api/v1/pois",
        json={"title": "Second stop", "location": {"lat": 52.3600, "lng": 4.8852}},
        headers=auth_headers,
    )
    poi2 = resp.json()
    route = client.post(
        "/api/v1/routes",
        json={
            "title": "Park walk",
            "is_public": True,
            "points": [{"poi_id": poi["id"]}, {"poi_id": poi2["id"]}],
        },
        headers=auth_headers,
    ).json()

    # Bob saves it (twice — idempotent)
    assert (
        client.post(f"/api/v1/routes/{route['id']}/save", headers=second_auth_headers).status_code
        == 204
    )
    client.post(f"/api/v1/routes/{route['id']}/save", headers=second_auth_headers)

    saved = client.get("/api/v1/routes/saved/mine", headers=second_auth_headers).json()
    assert [r["title"] for r in saved] == ["Park walk"]

    assert (
        client.delete(
            f"/api/v1/routes/{route['id']}/save", headers=second_auth_headers
        ).status_code
        == 204
    )
    assert client.get("/api/v1/routes/saved/mine", headers=second_auth_headers).json() == []
