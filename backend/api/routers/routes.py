import uuid

from django.contrib.gis.geos import LineString
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool

from api.deps import get_current_user, get_optional_user
from api.schemas.geo import LatLng
from api.schemas.pois import POIOut
from api.schemas.routes import RouteCreate, RouteOut, RoutePointOut
from apps.accounts.models import User
from apps.pois.models import PointOfInterest
from apps.routes.models import Route, RoutePoint, SavedRoute
from services.routing import ComputedRoute, compute_route, optimize_order

router = APIRouter()


def _route_out(route: Route, points: list[RoutePoint]) -> RouteOut:
    geometry = (
        [LatLng(lat=lat, lng=lng) for lng, lat in route.geometry.coords]
        if route.geometry
        else []
    )
    return RouteOut(
        id=route.id,
        title=route.title,
        description=route.description,
        route_type=route.route_type,
        transport_mode=route.transport_mode,
        theme_tags=route.theme_tags,
        total_distance_meters=route.total_distance_meters,
        estimated_duration_minutes=route.estimated_duration_minutes,
        difficulty_level=route.difficulty_level,
        is_public=route.is_public,
        geometry=geometry,
        points=[
            RoutePointOut(
                poi=POIOut.from_model(rp.poi),
                order_index=rp.order_index,
                stay_duration_minutes=rp.stay_duration_minutes,
                custom_note=rp.custom_note,
                distance_to_next_meters=rp.distance_to_next_meters,
                duration_to_next_minutes=rp.duration_to_next_minutes,
            )
            for rp in points
        ],
        created_at=route.created_at,
    )


@router.get("", response_model=list[RouteOut])
async def list_routes(
    mine: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User | None = Depends(get_optional_user),
) -> list[RouteOut]:
    if mine:
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
        qs = Route.objects.filter(created_by=user)
    else:
        qs = Route.objects.filter(is_public=True)
    qs = qs.order_by("-created_at")[offset : offset + limit]

    result = []
    async for route in qs:
        points = [rp async for rp in route.points.select_related("poi").all()]
        result.append(_route_out(route, points))
    return result


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
async def create_route(data: RouteCreate, user: User = Depends(get_current_user)) -> RouteOut:
    poi_ids = [p.poi_id for p in data.points]
    pois = {poi.id: poi async for poi in PointOfInterest.objects.filter(id__in=poi_ids)}
    missing = set(poi_ids) - set(pois)
    if missing:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown POIs: {missing}")

    ordered = list(data.points)
    coords = [(pois[p.poi_id].location.x, pois[p.poi_id].location.y) for p in ordered]
    if data.optimize_order or data.route_type == "auto":
        order = optimize_order(coords)
        ordered = [ordered[i] for i in order]
        coords = [coords[i] for i in order]

    computed: ComputedRoute = await compute_route(coords, data.transport_mode)

    stay_total = sum(p.stay_duration_minutes for p in ordered)

    def persist() -> tuple[Route, list[RoutePoint]]:
        with transaction.atomic():
            route = Route.objects.create(
                created_by_id=user.id,
                title=data.title,
                description=data.description,
                route_type=data.route_type,
                transport_mode=data.transport_mode,
                theme_tags=data.theme_tags,
                is_public=data.is_public,
                published_at=timezone.now() if data.is_public else None,
                total_distance_meters=computed.total_distance_m,
                estimated_duration_minutes=computed.total_duration_min + stay_total,
                geometry=LineString(computed.geometry, srid=4326)
                if len(computed.geometry) >= 2
                else None,
            )
            points = []
            for idx, p in enumerate(ordered):
                leg = computed.legs[idx] if idx < len(computed.legs) else None
                points.append(
                    RoutePoint.objects.create(
                        route=route,
                        poi_id=p.poi_id,
                        order_index=idx,
                        stay_duration_minutes=p.stay_duration_minutes,
                        custom_note=p.custom_note,
                        transport_to_next=data.transport_mode,
                        distance_to_next_meters=leg.distance_m if leg else 0,
                        duration_to_next_minutes=leg.duration_min if leg else 0,
                    )
                )
            return route, points

    route, points = await run_in_threadpool(persist)
    for rp in points:
        rp.poi = pois[rp.poi_id]
    return _route_out(route, points)


@router.post("/{route_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def save_route(route_id: uuid.UUID, user: User = Depends(get_current_user)) -> None:
    try:
        route = await Route.objects.aget(id=route_id)
    except Route.DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found") from None
    if not route.is_public and route.created_by_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found")
    _, created = await SavedRoute.objects.aget_or_create(route=route, user=user)
    if created:
        await Route.objects.filter(id=route.id).aupdate(save_count=F("save_count") + 1)


@router.delete("/{route_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_route(route_id: uuid.UUID, user: User = Depends(get_current_user)) -> None:
    deleted, _ = await SavedRoute.objects.filter(route_id=route_id, user=user).adelete()
    if deleted:
        await Route.objects.filter(id=route_id).aupdate(save_count=F("save_count") - 1)


@router.get("/saved/mine", response_model=list[RouteOut])
async def my_saved_routes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
) -> list[RouteOut]:
    result = []
    qs = (
        SavedRoute.objects.filter(user=user)
        .select_related("route")
        .order_by("-created_at")[offset : offset + limit]
    )
    async for saved in qs:
        points = [rp async for rp in saved.route.points.select_related("poi").all()]
        result.append(_route_out(saved.route, points))
    return result


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(
    route_id: uuid.UUID, user: User | None = Depends(get_optional_user)
) -> RouteOut:
    try:
        route = await Route.objects.aget(id=route_id)
    except Route.DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found") from None
    if not route.is_public and (user is None or route.created_by_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found")
    points = [rp async for rp in route.points.select_related("poi").all()]
    return _route_out(route, points)
