import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-do-not-use-in-production-0000")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "apps.accounts",
    "apps.businesses",
    "apps.pois",
    "apps.routes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "routehub"),
        "USER": os.environ.get("POSTGRES_USER", "routehub"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "routehub"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Redis / Celery ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "0") == "1"

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "reindex-search-nightly": {
        "task": "apps.pois.tasks.reindex_all_pois",
        "schedule": crontab(hour=3, minute=0),
    },
}

# --- JWT (consumed by the FastAPI layer) ---
JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TTL_MINUTES = int(os.environ.get("JWT_ACCESS_TTL_MINUTES", "30"))
JWT_REFRESH_TTL_DAYS = int(os.environ.get("JWT_REFRESH_TTL_DAYS", "14"))

# --- Geo / routing services ---
OSRM_URL = os.environ.get("OSRM_URL", "")  # empty -> straight-line fallback
NOMINATIM_URL = os.environ.get("NOMINATIM_URL", "https://nominatim.openstreetmap.org")

# --- Search (Meilisearch; empty MEILI_URL -> Postgres icontains fallback) ---
MEILI_URL = os.environ.get("MEILI_URL", "")
MEILI_MASTER_KEY = os.environ.get("MEILI_MASTER_KEY", "")
MEILI_INDEX_POIS = os.environ.get("MEILI_INDEX_POIS", "pois")

# --- Caching ---
POI_LIST_CACHE_TTL = int(os.environ.get("POI_LIST_CACHE_TTL", "60"))

# --- Embeddings (semantic search) ---
# "hash" = dependency-free dev backend; "fastembed" = real ONNX sentence embeddings
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND", "hash")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
