import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from api.schemas.geo import LatLng
from api.schemas.social import PublicUserOut


class POIBrief(BaseModel):
    id: uuid.UUID
    title: str
    city: str
    location: LatLng

    @classmethod
    def from_model(cls, poi) -> "POIBrief":
        return cls(
            id=poi.id,
            title=poi.title,
            city=poi.city,
            location=LatLng(lat=poi.location.y, lng=poi.location.x),
        )


class RouteSummary(BaseModel):
    id: uuid.UUID
    title: str
    transport_mode: str
    theme_tags: list[str]
    total_distance_meters: int
    estimated_duration_minutes: int

    model_config = {"from_attributes": True}


class FeedItemOut(BaseModel):
    type: Literal["checkin", "review", "route_published"]
    created_at: datetime
    actor: PublicUserOut
    poi: POIBrief | None = None
    route: RouteSummary | None = None
    comment: str = ""  # checkin
    rating: int | None = None  # review
    text: str = ""  # review
