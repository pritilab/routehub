import asyncio

from django.db.models import Q
from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool
from pgvector.django import CosineDistance

from api.schemas.pois import POIOut
from apps.pois.models import PointOfInterest
from services import search as search_service
from services.embeddings import embed_texts

router = APIRouter()


def _pg_keyword_qs(q: str):
    """Postgres keyword search — the fallback when Meilisearch is unavailable."""
    return PointOfInterest.objects.filter(
        Q(title__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q)
    ).order_by("-rating_avg", "-created_at")


async def _keyword_ids(q: str, fetch_k: int) -> list[str]:
    ids = await search_service.search_poi_ids(q, fetch_k)
    if ids is not None:
        return ids
    return [str(pid) async for pid in _pg_keyword_qs(q).values_list("id", flat=True)[:fetch_k]]


async def _semantic_ids(q: str, fetch_k: int) -> list[str]:
    query_vec = (await run_in_threadpool(embed_texts, [q]))[0]
    qs = (
        PointOfInterest.objects.exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_vec))
        .order_by("distance")
        .values_list("id", flat=True)[:fetch_k]
    )
    return [str(pid) async for pid in qs]


async def _fetch_ordered(ids: list[str]) -> list[POIOut]:
    pois = {str(p.id): p async for p in PointOfInterest.objects.filter(id__in=ids)}
    return [POIOut.from_model(pois[i]) for i in ids if i in pois]


@router.get("/pois/hybrid", response_model=list[POIOut])
async def hybrid_search_pois(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(20, ge=1, le=100),
    k: int = Query(60, ge=1, le=1000, description="RRF dampening constant"),
) -> list[POIOut]:
    """Keyword (Meilisearch) + semantic (pgvector) search fused with Reciprocal
    Rank Fusion. Degrades gracefully: either source being empty or down simply
    leaves the other one's ranking."""
    fetch_k = min(100, limit * 3)
    keyword, semantic = await asyncio.gather(
        _keyword_ids(q, fetch_k), _semantic_ids(q, fetch_k)
    )
    fused = search_service.rrf_merge([keyword, semantic], k=k)[:limit]
    return await _fetch_ordered(fused)


@router.get("/pois/semantic", response_model=list[POIOut])
async def semantic_search_pois(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(20, ge=1, le=100),
) -> list[POIOut]:
    """Meaning-based search over pgvector embeddings (HNSW, cosine distance).

    Only returns POIs that have been embedded (the enrich_poi Celery task
    fills embeddings shortly after creation).
    """
    return await _fetch_ordered(await _semantic_ids(q, limit))


@router.get("/pois", response_model=list[POIOut])
async def search_pois(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
) -> list[POIOut]:
    ids = await search_service.search_poi_ids(q, limit)

    if ids is not None:
        # Meilisearch answered: fetch from DB, keep relevance order, drop stale ids
        return await _fetch_ordered(ids)

    # Fallback: plain Postgres search (pg_trgm-friendly icontains)
    return [POIOut.from_model(poi) async for poi in _pg_keyword_qs(q)[:limit]]
