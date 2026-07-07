import pytest
from django.contrib.auth.hashers import make_password

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def bob_headers(db):
    from api.security import create_token
    from apps.accounts.models import User

    bob = User.objects.create(
        email="bob@example.com",
        username="bob",
        password=make_password("s3cretpass"),
        display_name="Bob",
    )
    return {"Authorization": f"Bearer {create_token(bob.id)}"}


@pytest.fixture
def charlie_headers(db):
    from api.security import create_token
    from apps.accounts.models import User

    charlie = User.objects.create(
        email="charlie@example.com",
        username="charlie",
        password=make_password("s3cretpass"),
    )
    return {"Authorization": f"Bearer {create_token(charlie.id)}"}


def make_poi(client, headers, title, lat=52.3728, lng=4.8936):
    resp = client.post(
        "/api/v1/pois",
        json={"title": title, "location": {"lat": lat, "lng": lng}},
        headers=headers,
    )
    return resp.json()


def test_feed_requires_auth(client):
    assert client.get("/api/v1/feed").status_code == 401


def test_feed_empty_when_following_nobody(client, auth_headers):
    assert client.get("/api/v1/feed", headers=auth_headers).json() == []


def test_feed_shows_followed_activity_only(client, auth_headers, bob_headers, charlie_headers):
    # Bob's activity: check-in, review, public route
    poi1 = make_poi(client, bob_headers, "Bob's cafe")
    poi2 = make_poi(client, bob_headers, "Bob's museum", lat=52.36)
    client.post(
        f"/api/v1/pois/{poi1['id']}/checkin", json={"comment": "Great espresso"},
        headers=bob_headers,
    )
    client.post(
        f"/api/v1/pois/{poi2['id']}/reviews", json={"rating": 5, "text": "A gem"},
        headers=bob_headers,
    )
    client.post(
        "/api/v1/routes",
        json={
            "title": "Bob's walk",
            "is_public": True,
            "points": [{"poi_id": poi1["id"]}, {"poi_id": poi2["id"]}],
        },
        headers=bob_headers,
    )
    # Charlie's activity must NOT appear (tester doesn't follow him)
    poi3 = make_poi(client, charlie_headers, "Charlie's bar")
    client.post(f"/api/v1/pois/{poi3['id']}/checkin", json={}, headers=charlie_headers)

    # Tester follows only Bob
    client.post("/api/v1/users/bob/follow", headers=auth_headers)

    items = client.get("/api/v1/feed", headers=auth_headers).json()
    assert sorted(i["type"] for i in items) == ["checkin", "review", "route_published"]
    assert {i["actor"]["username"] for i in items} == {"bob"}

    by_type = {i["type"]: i for i in items}
    assert by_type["checkin"]["comment"] == "Great espresso"
    assert by_type["checkin"]["poi"]["title"] == "Bob's cafe"
    assert by_type["review"]["rating"] == 5
    assert by_type["route_published"]["route"]["title"] == "Bob's walk"

    # Newest first
    timestamps = [i["created_at"] for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_private_routes_not_in_feed(client, auth_headers, bob_headers):
    poi1 = make_poi(client, bob_headers, "Stop A")
    poi2 = make_poi(client, bob_headers, "Stop B", lat=52.36)
    client.post(
        "/api/v1/routes",
        json={
            "title": "Bob's secret",
            "is_public": False,
            "points": [{"poi_id": poi1["id"]}, {"poi_id": poi2["id"]}],
        },
        headers=bob_headers,
    )
    client.post("/api/v1/users/bob/follow", headers=auth_headers)

    items = client.get("/api/v1/feed", headers=auth_headers).json()
    assert all(i["type"] != "route_published" for i in items)


def test_feed_pagination(client, auth_headers, bob_headers):
    poi = make_poi(client, bob_headers, "Busy place")
    for i in range(5):
        client.post(
            f"/api/v1/pois/{poi['id']}/checkin", json={"comment": f"visit {i}"},
            headers=bob_headers,
        )
    client.post("/api/v1/users/bob/follow", headers=auth_headers)

    page1 = client.get("/api/v1/feed", params={"limit": 2}, headers=auth_headers).json()
    page2 = client.get(
        "/api/v1/feed", params={"limit": 2, "offset": 2}, headers=auth_headers
    ).json()
    assert len(page1) == 2 and len(page2) == 2
    assert {i["comment"] for i in page1}.isdisjoint({i["comment"] for i in page2})
