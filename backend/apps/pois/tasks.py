import httpx
from celery import shared_task


@shared_task(autoretry_for=(httpx.HTTPError,), retry_backoff=True, max_retries=3)
def reindex_all_pois(batch_size: int = 500) -> int:
    """Full catalog rebuild of the Meilisearch index. Returns the number of POIs pushed.

    Runs nightly via celery beat; also available as `manage.py reindex_search`.
    """
    from services import search

    from .models import PointOfInterest

    if not search.enabled():
        return 0

    total = 0
    batch: list = []
    for poi in PointOfInterest.objects.iterator(chunk_size=batch_size):
        batch.append(poi)
        if len(batch) >= batch_size:
            search.index_pois_sync(batch)
            total += len(batch)
            batch = []
    if batch:
        search.index_pois_sync(batch)
        total += len(batch)
    return total


@shared_task
def enrich_poi(poi_id: str) -> bool:
    """Compute and store the pgvector embedding for a POI.

    (Future home for OSM/Overpass metadata enrichment as well.)
    """
    from services.embeddings import embed_texts, poi_document

    from .models import PointOfInterest

    poi = PointOfInterest.objects.filter(id=poi_id).first()
    if poi is None:
        return False
    poi.embedding = embed_texts([poi_document(poi)])[0]
    poi.save(update_fields=["embedding", "updated_at"])
    return True


@shared_task
def recompute_poi_rating(poi_id: str) -> None:
    from django.db.models import Avg, Count

    from .models import PointOfInterest, Review

    stats = Review.objects.filter(poi_id=poi_id).aggregate(avg=Avg("rating"), count=Count("id"))
    PointOfInterest.objects.filter(id=poi_id).update(
        rating_avg=stats["avg"] or 0.0, rating_count=stats["count"]
    )
