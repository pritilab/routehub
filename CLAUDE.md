# RouteHub — agent notes

Geo-social route platform. Django 5 (GeoDjango, models/admin) + FastAPI (API) in one
process; PostgreSQL 16 + PostGIS + pgvector; Celery/Redis; Vue 3 + Vite frontend.

## Commands (everything runs in Docker Compose)

- Run stack: `docker compose up --build`
- Tests: `docker compose run --rm backend pytest`
- Lint: `docker compose run --rm backend ruff check .`
- Migrations: `docker compose run --rm backend python manage.py makemigrations && docker compose run --rm backend python manage.py migrate`

Never run backend tests on the host — GDAL/PostGIS only exist in the containers.

## Conventions

- FastAPI endpoints use Django's **async ORM** (`aget`, `acreate`, `async for`); wrap
  multi-write transactions in a sync function via `run_in_threadpool` (see
  `api/routers/routes.py`).
- Coordinates: Pydantic side is `{lat, lng}`; PostGIS/GeoJSON side is `(lng, lat)` —
  `Point(lng, lat, srid=4326)`, `location.x` = lng, `location.y` = lat.
- New Django apps go under `apps/`, registered as `apps.<name>` in `INSTALLED_APPS`.
- Tests need `@pytest.mark.django_db(transaction=True)` because `TestClient` drives the
  app through the event loop (separate thread from pytest's transaction wrapper).
- pytest runs with `--no-migrations`; the `db` image installs postgis/vector/pg_trgm into
  `template1` so test databases inherit the extensions.
- Routing logic goes through `services/routing.py` (OSRM if `OSRM_URL` set, haversine
  fallback otherwise) — do not call OSRM directly from routers.
- External infra is always best-effort behind `services/`: `cache.py` (Redis, versioned
  namespaces — writers call `bump_version("pois")`), `search.py` (Meilisearch with Postgres
  fallback). Endpoints must keep working when Redis/Meili are down.
- Async Redis clients are cached per event loop in `services/cache.py` — a module-level
  singleton breaks under TestClient (one loop per test).
- Denormalized counters (`visit_count`, `save_count`, `rating_avg`) update via `F()`
  expressions / aggregate recompute in the endpoint that owns the write.
- Celery tasks live in `apps/<app>/tasks.py`; sync task code calls `search.index_pois_sync`
  (raises → autoretry), async endpoints call `search.index_pois` (best-effort, never raises).
  Beat schedule is `CELERY_BEAT_SCHEDULE` in settings; the `beat` compose service runs it.
- The feed (`api/routers/feed.py`) is a read-time merge over CheckIn/Review/Route filtered
  by `Follow` — no feed table yet.
- Embeddings go through `services/embeddings.py` (sync; call via `run_in_threadpool` from
  endpoints). `EMBEDDING_BACKEND=hash` is the dev/test default — tests rely on its
  token-overlap property for ranking assertions; don't switch tests to `fastembed`.
  Vector queries use `pgvector.django.CosineDistance` + the `poi_embedding_hnsw` index
  (`vector_cosine_ops` — keep operator class and query distance in sync).
