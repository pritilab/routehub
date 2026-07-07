import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=150, pattern=r"^[\w.@+-]+$")
    password: str = Field(min_length=8)
    display_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    display_name: str
    avatar_url: str
    bio: str
    role: str

    model_config = {"from_attributes": True}
