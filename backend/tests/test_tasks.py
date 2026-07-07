import pytest
from django.contrib.gis.geos import Point

pytestmark = pytest.mark.django_db(transaction=True)


def test_reindex_all_pois(user):
    """Celery reindex task pushes every POI to Meilisearch and reports the count.
    POIs are created via the ORM (bypassing the API's inline indexing) to prove
    the rebuild itself works."""
    from apps.pois.models import PointOfInterest
    from apps.pois.tasks import reindex_all_pois
    from services import search

    for i in range(3):
        PointOfInterest.objects.create(
            created_by=user,
            title=f"Reindex target {i}",
            location=Point(4.89 + i * 0.001, 52.37, srid=4326),
        )

    count = reindex_all_pois()
    if search.enabled():
        assert count == 3
    else:
        assert count == 0  # graceful no-op without MEILI_URL


def test_recompute_poi_rating(user):
    from apps.pois.models import PointOfInterest, Review
    from apps.pois.tasks import recompute_poi_rating

    poi = PointOfInterest.objects.create(
        created_by=user, title="Rated", location=Point(4.89, 52.37, srid=4326)
    )
    Review.objects.create(poi=poi, user=user, rating=4)
    recompute_poi_rating(str(poi.id))

    poi.refresh_from_db()
    assert poi.rating_avg == 4.0
    assert poi.rating_count == 1
