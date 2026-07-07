import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.geo import LatLng
from api.schemas.pois import POIOut


class RoutePointIn(BaseModel):
    poi_id: uuid.UUID
    stay_duration_minutes: int = 0
    custom_note: str = ""


class RouteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    route_type: str = "manual"  # auto | semi_auto | manual
    transport_mode: str = "walking"
    theme_tags: list[str] = []
    is_public: bool = False
    points: list[RoutePointIn] = Field(min_length=2)
    optimize_order: bool = False  # auto mode: let the backend reorder stops


class RoutePointOut(BaseModel):
    poi: POIOut
    order_index: int
    stay_duration_minutes: int
    custom_note: str
    distance_to_next_meters: int
    duration_to_next_minutes: int


class RouteOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    route_type: str
    transport_mode: str
    theme_tags: list[str]
    total_distance_meters: int
    estimated_duration_minutes: int
    difficulty_level: str
    is_public: bool
    geometry: list[LatLng]  # ordered path polyline
    points: list[RoutePointOut]
    created_at: datetime
