import pytest

pytestmark = pytest.mark.django_db(transaction=True)

AMSTERDAM_CENTER = {"lat": 52.3728, "lng": 4.8936}


def make_poi(client, auth_headers, title="Test POI", lat=52.3728, lng=4.8936, **extra):
    payload = {
        "title": title,
        "location": {"lat": lat, "lng": lng},
        "city": "Amsterdam",
        "categories": ["cafe"],
        **extra,
    }
    resp = client.post("/api/v1/pois", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_requires_auth(client):
    resp = client.post(
        "/api/v1/pois", json={"title": "X", "location": AMSTERDAM_CENTER}
    )
    assert resp.status_code == 401


def test_create_and_get(client, auth_headers):
    poi = make_poi(client, auth_headers)
    assert poi["title"] == "Test POI"
    assert abs(poi["location"]["lat"] - 52.3728) < 1e-6

    resp = client.get(f"/api/v1/pois/{poi['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == poi["id"]


def test_nearby_search(client, auth_headers):
    make_poi(client, auth_headers, title="Dam Square", lat=52.3731, lng=4.8926)
    make_poi(client, auth_headers, title="Rotterdam Markthal", lat=51.9200, lng=4.4870)

    resp = client.get(
        "/api/v1/pois",
        params={"lat": 52.3728, "lng": 4.8936, "radius_m": 5000},
    )
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert "Dam Square" in titles
    assert "Rotterdam Markthal" not in titles


def test_category_filter(client, auth_headers):
    make_poi(client, auth_headers, title="Museum", categories=["museum"])
    make_poi(client, auth_headers, title="Cafe", categories=["cafe"])

    resp = client.get("/api/v1/pois", params={"category": "museum"})
    titles = [p["title"] for p in resp.json()]
    assert titles == ["Museum"]
