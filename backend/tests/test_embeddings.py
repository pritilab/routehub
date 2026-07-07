import math

import pytest
from django.contrib.gis.geos import Point

pytestmark = pytest.mark.django_db(transaction=True)


def create_poi(user, title, description=""):
    from apps.pois.models import PointOfInterest

    return PointOfInterest.objects.create(
        created_by=user,
        title=title,
        description=description,
        location=Point(4.89, 52.37, srid=4326),
    )


def test_embed_texts_shape_and_norm():
    from services.embeddings import embed_texts

    vecs = embed_texts(["coffee espresso bar", "medieval castle"])
    assert len(vecs) == 2
    assert all(len(v) == 384 for v in vecs)
    for v in vecs:
        assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0, rel_tol=1e-6)


def test_enrich_poi_stores_embedding(user):
    from apps.pois.tasks import enrich_poi

    poi = create_poi(user, "Coffee espresso bar")
    assert poi.embedding is None
    assert enrich_poi(str(poi.id)) is True

    poi.refresh_from_db()
    assert poi.embedding is not None
    assert len(poi.embedding) == 384


def test_enrich_missing_poi_is_noop():
    from apps.pois.tasks import enrich_poi

    assert enrich_poi("00000000-0000-0000-0000-000000000000") is False


def test_semantic_search_ranks_by_meaning(client, user):
    from apps.pois.tasks import enrich_poi

    coffee = create_poi(user, "Specialty coffee espresso bar", "flat white and filter coffee")
    castle = create_poi(user, "Medieval castle museum", "knights armor and ancient walls")
    for poi in (coffee, castle):
        enrich_poi(str(poi.id))

    resp = client.get("/api/v1/search/pois/semantic", params={"q": "espresso coffee place"})
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert titles[0] == "Specialty coffee espresso bar"


def test_similar_pois(client, user):
    from apps.pois.tasks import enrich_poi

    a = create_poi(user, "Coffee espresso bar", "espresso cappuccino coffee beans")
    b = create_poi(user, "Coffee roastery cafe", "coffee espresso brewing")
    c = create_poi(user, "Medieval castle museum", "knights armor towers")
    for poi in (a, b, c):
        enrich_poi(str(poi.id))

    resp = client.get(f"/api/v1/pois/{a.id}/similar")
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert titles[0] == "Coffee roastery cafe"
    assert str(a.id) not in [p["id"] for p in resp.json()]


def test_similar_before_embedding_is_empty(client, user):
    poi = create_poi(user, "Fresh place")
    resp = client.get(f"/api/v1/pois/{poi.id}/similar")
    assert resp.status_code == 200
    assert resp.json() == []
