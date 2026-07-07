from fastapi import APIRouter, Depends, Query

from api.deps import get_current_user
from api.schemas.feed import FeedItemOut, POIBrief, RouteSummary
from api.schemas.social import PublicUserOut
from apps.accounts.models import Follow, User
from apps.pois.models import CheckIn, Review
from apps.routes.models import Route

router = APIRouter()


@router.get("", response_model=list[FeedItemOut])
async def feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
) -> list[FeedItemOut]:
    """Merged recent activity of everyone the caller follows.

    Each source is over-fetched to offset+limit, merged by recency, then sliced —
    fine at this scale; swap for a fan-out-on-write feed table when it gets hot.
    """
    followee_ids = [
        fid
        async for fid in Follow.objects.filter(follower=user).values_list(
            "followee_id", flat=True
        )
    ]
    if not followee_ids:
        return []

    window = offset + limit
    items: list[FeedItemOut] = []

    checkins = (
        CheckIn.objects.filter(user_id__in=followee_ids)
        .select_related("user", "poi")
        .order_by("-created_at")[:window]
    )
    async for c in checkins:
        items.append(
            FeedItemOut(
                type="checkin",
                created_at=c.created_at,
                actor=PublicUserOut.model_validate(c.user),
                poi=POIBrief.from_model(c.poi),
                comment=c.comment,
            )
        )

    reviews = (
        Review.objects.filter(user_id__in=followee_ids)
        .select_related("user", "poi")
        .order_by("-created_at")[:window]
    )
    async for r in reviews:
        items.append(
            FeedItemOut(
                type="review",
                created_at=r.created_at,
                actor=PublicUserOut.model_validate(r.user),
                poi=POIBrief.from_model(r.poi),
                rating=r.rating,
                text=r.text,
            )
        )

    routes = (
        Route.objects.filter(created_by_id__in=followee_ids, is_public=True)
        .select_related("created_by")
        .order_by("-created_at")[:window]
    )
    async for route in routes:
        items.append(
            FeedItemOut(
                type="route_published",
                created_at=route.published_at or route.created_at,
                actor=PublicUserOut.model_validate(route.created_by),
                route=RouteSummary.model_validate(route),
            )
        )

    items.sort(key=lambda i: i.created_at, reverse=True)
    return items[offset : offset + limit]
