from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings


def create_token(user_id: str, token_type: str = "access") -> str:
    if token_type == "access":
        ttl = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    else:
        ttl = timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload
