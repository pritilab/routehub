import jwt
from django.contrib.auth.hashers import check_password, make_password
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_current_user
from api.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut
from api.security import create_token, decode_token
from apps.accounts.models import User

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn) -> User:
    if await User.objects.filter(email=data.email).aexists():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if await User.objects.filter(username=data.username).aexists():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username taken")
    return await User.objects.acreate(
        email=data.email,
        username=data.username,
        password=make_password(data.password),
        display_name=data.display_name or data.username,
    )


@router.post("/login", response_model=TokenPair)
async def login(data: LoginIn) -> TokenPair:
    try:
        user = await User.objects.aget(email=data.email, is_active=True)
    except User.DoesNotExist:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials") from None
    if not check_password(data.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenPair(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshIn) -> TokenPair:
    try:
        payload = decode_token(data.refresh_token, expected_type="refresh")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from None
    return TokenPair(
        access_token=create_token(payload["sub"], "access"),
        refresh_token=create_token(payload["sub"], "refresh"),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
