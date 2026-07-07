import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.asgi import get_asgi_application  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.routers import auth, feed, health, pois, routes, search, users  # noqa: E402

app = FastAPI(
    title="RouteHub API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(pois.router, prefix="/api/v1/pois", tags=["pois"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["routes"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(feed.router, prefix="/api/v1/feed", tags=["feed"])

# Django admin (and anything else Django serves) lives under the same process.
app.mount("/", get_asgi_application())
