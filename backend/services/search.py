"""POI full-text search: Meilisearch when configured, Postgres icontains fallback.

Indexing is best-effort — a down search engine must never fail a write path.
"""

import httpx
from django.conf import settings


def enabled() -> bool:
    return bool(settings.MEILI_URL)


def rrf_merge(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal Rank Fusion: score(doc) = sum over rankings of 1/(k + rank).

    Docs appearing high in multiple rankings win; k dampens the head advantage.
    Ties break by first appearance order, so the result is deterministic.
    """
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            first_seen.setdefault(doc_id, len(first_seen))
    return sorted(scores, key=lambda d: (-scores[d], first_seen[d]))


def _headers() -> dict:
    if settings.MEILI_MASTER_KEY:
        return {"Authorization": f"Bearer {settings.MEILI_MASTER_KEY}"}
    return {}


def _doc(poi) -> dict:
    return {
        "id": str(poi.id),
        "title": poi.title,
        "description": poi.description,
        "short_description": poi.short_description,
        "city": poi.city,
        "country": poi.country,
        "categories": poi.categories,
    }


async def index_pois(pois) -> None:
    """Add/update POIs in the search index. Silently no-ops if Meili is off/down."""
    if not enabled() or not pois:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{settings.MEILI_URL}/indexes/{settings.MEILI_INDEX_POIS}/documents",
                json=[_doc(p) for p in pois],
                headers=_headers(),
            )
    except httpx.HTTPError:
        pass


def index_pois_sync(pois) -> None:
    """Synchronous variant for Celery tasks. Raises on failure so the task can retry."""
    if not enabled() or not pois:
        return
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{settings.MEILI_URL}/indexes/{settings.MEILI_INDEX_POIS}/documents",
            json=[_doc(p) for p in pois],
            headers=_headers(),
        )
        resp.raise_for_status()


async def delete_poi(poi_id: str) -> None:
    if not enabled():
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.delete(
                f"{settings.MEILI_URL}/indexes/{settings.MEILI_INDEX_POIS}/documents/{poi_id}",
                headers=_headers(),
            )
    except httpx.HTTPError:
        pass


async def search_poi_ids(query: str, limit: int = 20) -> list[str] | None:
    """Return matching POI ids in relevance order, or None if Meili is unavailable
    (caller should fall back to a database search)."""
    if not enabled():
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"{settings.MEILI_URL}/indexes/{settings.MEILI_INDEX_POIS}/search",
                json={"q": query, "limit": limit},
                headers=_headers(),
            )
            if resp.status_code == 404:  # index not created yet
                return []
            resp.raise_for_status()
            return [hit["id"] for hit in resp.json()["hits"]]
    except (httpx.HTTPError, KeyError):
        return None
