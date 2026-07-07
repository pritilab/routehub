import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.geo import LatLng


class POICreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    short_description: str = Field(default="", max_length=280)
    location: LatLng
    address: str = ""
    city: str = ""
    country: str = ""
    postal_code: str = ""
    categories: list[str] = []
    photos: list[str] = []
    is_temporary: bool = False
    active_from: datetime | None = None
    active_until: datetime | None = None
    metadata: dict = {}


class POIOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    short_description: str
    location: LatLng
    address: str
    city: str
    country: str
    categories: list[str]
    photos: list[str]
    is_official: bool
    is_temporary: bool
    rating_avg: float
    rating_count: int
    visit_count: int
    save_count: int
    metadata: dict
    created_at: datetime

    @classmethod
    def from_model(cls, poi) -> "POIOut":
        return cls(
            id=poi.id,
            title=poi.title,
            description=poi.description,
            short_description=poi.short_description,
            location=LatLng(lat=poi.location.y, lng=poi.location.x),
            address=poi.address,
            city=poi.city,
            country=poi.country,
            categories=poi.categories,
            photos=poi.photos,
            is_official=poi.is_official,
            is_temporary=poi.is_temporary,
            rating_avg=poi.rating_avg,
            rating_count=poi.rating_count,
            visit_count=poi.visit_count,
            save_count=poi.save_count,
            metadata=poi.metadata,
            created_at=poi.created_at,
        )
