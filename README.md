# RouteHub

Geo-social platform: users and businesses place points of interest (POI) on the map,
the system builds optimized routes — automatically or hand-curated. Social layer on top:
follows, check-ins, saved routes, collaboration.

## Stack

| Layer      | Tech                                                      |
|------------|-----------------------------------------------------------|
| Models/ORM | Django 5 (GeoDjango) — models, migrations, admin          |
| API        | FastAPI (async), mounted in the same process, JWT auth    |
| Database   | PostgreSQL 16 + PostGIS + pgvector                        |
| Queue      | Celery + Redis (worker + beat)                            |
| Routing    | OSRM (optional, self-hosted) with straight-line fallback  |
| Search     | Meilisearch with Postgres icontains fallback              |
| Frontend   | Vue 3 + Vite + Pinia + Tailwind CSS 4 + Mapbox GL JS      |

## Quickstart

```bash
cp .env.example .env        # adjust secrets, add VITE_MAPBOX_TOKEN for the map
docker compose up --build
```

First run — create schema and admin user:

```bash
docker compose run --rm backend python manage.py makemigrations accounts businesses pois routes
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py createsuperuser
```

Then:

- Frontend: <http://localhost:5173>
- API docs (Swagger): <http://localhost:8000/api/docs>
- Django admin: <http://localhost:8000/admin/>
- Health check: <http://localhost:8000/api/v1/health>

If port 8000 is busy on your machine, set `BACKEND_PORT` in `.env` (the container
always listens on 8000 internally).

## Tests

All tests run inside Docker Compose:

```bash
docker compose run --rm backend pytest
docker compose run --rm backend ruff check .
```

Tests use `--no-migrations` (tables created directly from models), so they work
even before migrations are generated. PostGIS/pgvector extensions are installed
into `template1`, so pytest's throwaway test database inherits them.

## Architecture notes

- **One backend process, two frameworks.** `api/main.py` boots Django (`django.setup()`),
  serves the FastAPI app under `/api/*`, and mounts Django's ASGI app at `/` for the admin.
  FastAPI endpoints use Django's async ORM (`aget`, `acreate`, `async for`).
- **Route computation** lives in `services/routing.py`. If `OSRM_URL` is set, routes follow
  real streets via OSRM; otherwise a haversine straight-line fallback keeps everything working
  in dev. `route_type: auto` (or `optimize_order: true`) reorders stops with a
  nearest-neighbor heuristic.
- **Geo queries**: POI search supports `lat/lng/radius_m` (distance-sorted) and `bbox` filters
  backed by PostGIS GiST indexes.
- **Semantic search (pgvector)**: on POI create the API enqueues `enrich_poi`, the Celery
  worker embeds `title + descriptions + categories + city` into `embedding` (384 dims,
  HNSW index, cosine distance). `GET /api/v1/search/pois/semantic?q=` searches by meaning;
  `GET /api/v1/pois/{id}/similar` returns nearest neighbors. Two embedding backends
  (`EMBEDDING_BACKEND`): `hash` — instant, dependency-free hashing trick for dev/tests;
  `fastembed` — real ONNX sentence embeddings (`BAAI/bge-small-en-v1.5`, downloads the
  model on first use).
- **POI list caching** (`services/cache.py`): geo list queries are cached in Redis with a
  versioned namespace — writers (`create_poi`, reviews, check-ins) bump the version, readers
  include it in the key, stale entries just expire by TTL. All cache ops are best-effort:
  Redis being down never breaks reads.
- **Full-text search** (`services/search.py`, `GET /api/v1/search/pois?q=`): POIs are indexed
  into Meilisearch on create (best-effort); if Meili is unreachable the endpoint transparently
  falls back to Postgres `icontains`.
- **Hybrid search** (`GET /api/v1/search/pois/hybrid?q=`): keyword and semantic rankings
  fetched concurrently and fused with Reciprocal Rank Fusion (`rrf_merge`, tunable `k`).
  POIs relevant on both channels rank first; either channel being empty or down simply
  leaves the other's ranking.
- **Social layer**: `POST/DELETE /users/{username}/follow` (+ followers/following lists),
  `POST /pois/{id}/checkin` (bumps `visit_count`), `POST /pois/{id}/reviews` (upsert, recomputes
  the denormalized rating), `POST/DELETE /routes/{id}/save` + `GET /routes/saved/mine`.
- **Activity feed** (`GET /api/v1/feed`): merged check-ins, reviews and published routes of
  everyone you follow, newest first. Read-time merge (over-fetch each source, sort, slice) —
  swap for a fan-out-on-write feed table when it gets hot.
- **Celery**: `worker` runs tasks, `beat` schedules a nightly (03:00 UTC) full Meilisearch
  reindex (`apps.pois.tasks.reindex_all_pois`, batched, auto-retry with backoff). Manual
  rebuild: `docker compose run --rm backend python manage.py reindex_search`.

## Routing engine (optional)

To run real street routing, download an OSM extract and preprocess it:

```bash
mkdir osrm-data && cd osrm-data
# example: Netherlands
curl -O https://download.geofabrik.de/europe/netherlands-latest.osm.pbf
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/netherlands-latest.osm.pbf
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-partition /data/netherlands-latest.osrm
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-customize /data/netherlands-latest.osrm
mv netherlands-latest.osrm map.osrm  # or adjust the compose command
```

Then set `OSRM_URL=http://osrm:5000` in `.env` and start with the routing profile:

```bash
docker compose --profile routing up
```

## Project layout

```text
backend/
  config/          # Django settings, ASGI, Celery
  apps/
    accounts/      # User (UUID, roles, geo home), Follow
    businesses/    # Business profiles, subscription tiers
    pois/          # POI (PostGIS point, pgvector embedding), Review, CheckIn
    routes/        # Route (LINESTRING), RoutePoint, RouteCollaborator, SavedRoute
  api/             # FastAPI: routers, schemas, JWT security
  services/        # routing (OSRM/fallback), future: geocoding, search
  tests/           # pytest (runs in docker compose)
frontend/          # Vue 3 + Vite + Pinia + Tailwind + Mapbox GL
  src/pages/       #   Home (public routes), Search (hybrid), Map, Feed, Profile, Login
db/                # PostGIS+pgvector image, extension init
```
