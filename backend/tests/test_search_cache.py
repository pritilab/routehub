import time

import pytest

pytestmark = pytest.mark.django_db(transaction=True)


def make_poi(client, auth_headers, title, lat=52.3728, lng=4.8936, **extra):
    resp = client.post(
        "/api/v1/pois",
        json={"title": title, "location": {"lat": lat, "lng": lng}, **extra},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_poi_list_cache_invalidated_on_create(client, auth_headers):
    """The nearby list is cached in Redis; creating a POI must bump the version
    so the next read sees fresh data instead of a stale cached page."""
    params = {"lat": 52.3728, "lng": 4.8936, "radius_m": 5000}

    make_poi(client, auth_headers, "First cafe")
    first = client.get("/api/v1/pois", params=params).json()
    assert [p["title"] for p in first] == ["First cafe"]

    # Warm the cache, then write
    client.get("/api/v1/pois", params=params)
    make_poi(client, auth_headers, "Second cafe", lat=52.3730)

    second = client.get("/api/v1/pois", params=params).json()
    assert sorted(p["title"] for p in second) == ["First cafe", "Second cafe"]


def test_poi_list_cache_invalidated_on_review(client, auth_headers):
    poi = make_poi(client, auth_headers, "Rated place")
    params = {"lat": 52.3728, "lng": 4.8936, "radius_m": 5000}
    client.get("/api/v1/pois", params=params)  # warm cache

    client.post(f"/api/v1/pois/{poi['id']}/reviews", json={"rating": 5}, headers=auth_headers)

    listed = client.get("/api/v1/pois", params=params).json()
    assert listed[0]["rating_avg"] == 5.0


def test_rrf_merge_prefers_docs_ranked_in_both():
    from services.search import rrf_merge

    # "b" appears in both rankings -> must beat "a" (top of one) and "c" (tail of one)
    fused = rrf_merge([["a", "b"], ["b", "c"]])
    assert fused == ["b", "a", "c"]


def test_rrf_merge_deterministic_tie_break():
    from services.search import rrf_merge

    assert rrf_merge([["x"], ["y"]]) == ["x", "y"]
    assert rrf_merge([["y"], ["x"]]) == ["y", "x"]


def test_hybrid_search(client, auth_headers):
    """Hybrid = keyword (Meili or PG fallback) + semantic (pgvector) fused via RRF.
    The coffee POI is relevant on both channels and must rank first; embeddings
    are computed inline via the task since no worker runs during tests."""
    from apps.pois.tasks import enrich_poi

    coffee = make_poi(
        client, auth_headers, "Specialty espresso coffee bar",
        description="flat white and filter coffee",
    )
    castle = make_poi(
        client, auth_headers, "Medieval castle museum",
        description="knights armor and ancient walls",
    )
    for poi in (coffee, castle):
        enrich_poi(poi["id"])

    deadline = time.monotonic() + 10
    titles = []
    while time.monotonic() < deadline:
        resp = client.get("/api/v1/search/pois/hybrid", params={"q": "espresso coffee"})
        assert resp.status_code == 200
        titles = [p["title"] for p in resp.json()]
        if titles and titles[0] == "Specialty espresso coffee bar":
            break
        time.sleep(0.5)
    assert titles and titles[0] == "Specialty espresso coffee bar"


def test_search_pois(client, auth_headers):
    """Works against Meilisearch when it's up (indexing is async, so poll),
    and against the Postgres fallback otherwise."""
    make_poi(client, auth_headers, "Stedelijk Modern Art Museum", city="Amsterdam")
    make_poi(client, auth_headers, "Brouwerij 't IJ", city="Amsterdam")

    deadline = time.monotonic() + 10
    titles = []
    while time.monotonic() < deadline:
        resp = client.get("/api/v1/search/pois", params={"q": "modern art"})
        assert resp.status_code == 200
        titles = [p["title"] for p in resp.json()]
        if "Stedelijk Modern Art Museum" in titles:
            break
        time.sleep(0.5)
    assert "Stedelijk Modern Art Museum" in titles
    assert "Brouwerij 't IJ" not in titles
