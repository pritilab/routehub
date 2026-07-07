import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PublicUserOut(BaseModel):
    """User as visible to others — no email."""

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str

    model_config = {"from_attributes": True}


class ProfileOut(PublicUserOut):
    bio: str
    role: str
    followers_count: int
    following_count: int
    is_following: bool | None = None  # null when viewed anonymously


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = ""


class ReviewOut(BaseModel):
    id: uuid.UUID
    user: PublicUserOut
    rating: int
    text: str
    created_at: datetime


class CheckInIn(BaseModel):
    comment: str = Field(default="", max_length=280)


class CheckInOut(BaseModel):
    id: uuid.UUID
    poi_id: uuid.UUID
    user: PublicUserOut
    comment: str
    created_at: datetime
