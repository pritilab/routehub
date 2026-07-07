import pytest

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def three_pois(client, auth_headers):
    """Three POIs in Amsterdam, deliberately given out of walking order."""
    coords = [
        ("Dam Square", 52.3731, 4.8926),
        ("Rijksmuseum", 52.3600, 4.8852),
        ("Anne Frank House", 52.3752, 4.8840),
    ]
    ids = []
    for title, lat, lng in coords:
        resp = client.post(
            "/api/v1/pois",
            json={"title": title, "location": {"lat": lat, "lng": lng}, "city": "Amsterdam"},
            headers=auth_headers,
        )
        ids.append(resp.json()["id"])
    return ids


def test_create_route(client, auth_headers, three_pois):
    resp = client.post(
        "/api/v1/routes",
        json={
            "title": "Amsterdam classics",
            "transport_mode": "walking",
            "is_public": True,
            "points": [{"poi_id": pid, "stay_duration_minutes": 30} for pid in three_pois],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    route = resp.json()
    assert len(route["points"]) == 3
    assert route["total_distance_meters"] > 0
    # 3 stops x 30 min stay + travel time
    assert route["estimated_duration_minutes"] > 90
    assert len(route["geometry"]) >= 2


def test_auto_route_optimizes_order(client, auth_headers, three_pois):
    resp = client.post(
        "/api/v1/routes",
        json={
            "title": "Optimized",
            "route_type": "auto",
            "points": [{"poi_id": pid} for pid in three_pois],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    titles = [p["poi"]["title"] for p in resp.json()["points"]]
    # From Dam Square, Anne Frank House (~700m) is closer than Rijksmuseum (~1.5km)
    assert titles == ["Dam Square", "Anne Frank House", "Rijksmuseum"]


def test_private_route_hidden(client, auth_headers, three_pois):
    resp = client.post(
        "/api/v1/routes",
        json={
            "title": "Secret route",
            "is_public": False,
            "points": [{"poi_id": pid} for pid in three_pois[:2]],
        },
        headers=auth_headers,
    )
    route_id = resp.json()["id"]

    # Anonymous access -> 404
    assert client.get(f"/api/v1/routes/{route_id}").status_code == 404
    # Owner -> 200
    assert client.get(f"/api/v1/routes/{route_id}", headers=auth_headers).status_code == 200
    # Not in the public listing
    listing = client.get("/api/v1/routes").json()
    assert all(r["title"] != "Secret route" for r in listing)


def test_route_needs_two_points(client, auth_headers, three_pois):
    resp = client.post(
        "/api/v1/routes",
        json={"title": "Too short", "points": [{"poi_id": three_pois[0]}]},
        headers=auth_headers,
    )
    assert resp.status_code == 422
