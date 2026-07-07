import uuid

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db.models import Avg, Count, F
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user
from api.schemas.pois import POICreate, POIOut
from api.schemas.social import CheckInIn, CheckInOut, PublicUserOut, ReviewIn, ReviewOut
from apps.accounts.models import User
from apps.pois.models import CheckIn, PointOfInterest, Review
from apps.pois.tasks import enrich_poi
from services import cache, search

router = APIRouter()

MAX_PAGE_SIZE = 100
CACHE_NS = "pois"


async def _get_poi_or_404(poi_id: uuid.UUID) -> PointOfInterest:
    try:
        return await PointOfInterest.objects.aget(id=poi_id)
    except PointOfInterest.DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "POI not found") from None


@router.get("", response_model=list[POIOut])
async def list_pois(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_m: int = Query(2000, ge=1, le=50_000),
    bbox: str | None = Query(None, description="minLng,minLat,maxLng,maxLat"),
    city: str | None = None,
    category: str | None = None,
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> list:
    params = {
        "lat": lat, "lng": lng, "radius_m": radius_m, "bbox": bbox,
        "city": city, "category": category, "limit": limit, "offset": offset,
    }
    cached = await cache.get_cached(CACHE_NS, params)
    if cached is not None:
        return cached

    qs = PointOfInterest.objects.all()

    if lat is not None and lng is not None:
        origin = Point(lng, lat, srid=4326)
        qs = (
            qs.filter(location__distance_lte=(origin, D(m=radius_m)))
            .annotate(distance=Distance("location", origin))
            .order_by("distance")
        )
    elif bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = (float(v) for v in bbox.split(","))
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "bbox must be minLng,minLat,maxLng,maxLat"
            ) from None
        qs = qs.filter(location__within=Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat)))
    else:
        qs = qs.order_by("-created_at")

    if city:
        qs = qs.filter(city__iexact=city)
    if category:
        qs = qs.filter(categories__contains=[category])

    result = [POIOut.from_model(poi) async for poi in qs[offset : offset + limit]]
    await cache.set_cached(CACHE_NS, params, [p.model_dump(mode="json") for p in result])
    return result


@router.post("", response_model=POIOut, status_code=status.HTTP_201_CREATED)
async def create_poi(data: POICreate, user: User = Depends(get_current_user)) -> POIOut:
    poi = await PointOfInterest.objects.acreate(
        created_by=user,
        title=data.title,
        description=data.description,
        short_description=data.short_description,
        location=Point(data.location.lng, data.location.lat, srid=4326),
        address=data.address,
        city=data.city,
        country=data.country,
        postal_code=data.postal_code,
        categories=data.categories,
        photos=data.photos,
        is_temporary=data.is_temporary,
        active_from=data.active_from,
        active_until=data.active_until,
        metadata=data.metadata,
    )
    await cache.bump_version(CACHE_NS)
    await search.index_pois([poi])  # best-effort
    try:
        enrich_poi.delay(str(poi.id))  # embedding computed by the worker
    except Exception:
        pass  # broker down must not fail the write
    return POIOut.from_model(poi)


@router.get("/{poi_id}", response_model=POIOut)
async def get_poi(poi_id: uuid.UUID) -> POIOut:
    return POIOut.from_model(await _get_poi_or_404(poi_id))


@router.get("/{poi_id}/similar", response_model=list[POIOut])
async def similar_pois(
    poi_id: uuid.UUID, limit: int = Query(10, ge=1, le=50)
) -> list[POIOut]:
    """POIs semantically closest to this one (pgvector cosine distance).

    Empty until the POI's embedding has been computed by the worker.
    """
    from pgvector.django import CosineDistance

    poi = await _get_poi_or_404(poi_id)
    if poi.embedding is None:
        return []
    qs = (
        PointOfInterest.objects.exclude(id=poi.id)
        .exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", poi.embedding))
        .order_by("distance")[:limit]
    )
    return [POIOut.from_model(p) async for p in qs]


# --- Social layer -----------------------------------------------------------


@router.post(
    "/{poi_id}/checkin", response_model=CheckInOut, status_code=status.HTTP_201_CREATED
)
async def check_in(
    poi_id: uuid.UUID, data: CheckInIn, user: User = Depends(get_current_user)
) -> CheckInOut:
    poi = await _get_poi_or_404(poi_id)
    checkin = await CheckIn.objects.acreate(poi=poi, user=user, comment=data.comment)
    await PointOfInterest.objects.filter(id=poi.id).aupdate(visit_count=F("visit_count") + 1)
    await cache.bump_version(CACHE_NS)
    return CheckInOut(
        id=checkin.id,
        poi_id=poi.id,
        user=PublicUserOut.model_validate(user),
        comment=checkin.comment,
        created_at=checkin.created_at,
    )


@router.post(
    "/{poi_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
async def upsert_review(
    poi_id: uuid.UUID, data: ReviewIn, user: User = Depends(get_current_user)
) -> ReviewOut:
    """Create or update the caller's review; recomputes the POI's denormalized rating."""
    poi = await _get_poi_or_404(poi_id)
    review, _ = await Review.objects.aupdate_or_create(
        poi=poi, user=user, defaults={"rating": data.rating, "text": data.text}
    )
    stats = await Review.objects.filter(poi=poi).aaggregate(avg=Avg("rating"), count=Count("id"))
    await PointOfInterest.objects.filter(id=poi.id).aupdate(
        rating_avg=stats["avg"] or 0.0, rating_count=stats["count"]
    )
    await cache.bump_version(CACHE_NS)
    return ReviewOut(
        id=review.id,
        user=PublicUserOut.model_validate(user),
        rating=review.rating,
        text=review.text,
        created_at=review.created_at,
    )


@router.get("/{poi_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(
    poi_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ReviewOut]:
    poi = await _get_poi_or_404(poi_id)
    qs = (
        Review.objects.filter(poi=poi)
        .select_related("user")
        .order_by("-created_at")[offset : offset + limit]
    )
    return [
        ReviewOut(
            id=r.id,
            user=PublicUserOut.model_validate(r.user),
            rating=r.rating,
            text=r.text,
            created_at=r.created_at,
        )
        async for r in qs
    ]
