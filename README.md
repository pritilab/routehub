# RouteHub

Geo-social route platform: users and businesses place points of interest (POI) on the map,
the system builds optimized routes — automatically or hand-curated. Rich social layer: follow users,
check in at places, review POIs, save routes, and stay updated via a personalized feed.

**Repository**: [pritilab/routehub](https://github.com/pritilab/routehub)

---

## Stack

| Layer      | Tech                                                      |
|------------|-----------------------------------------------------------|
| Models/ORM | Django 5 (GeoDjango) — models, migrations, admin          |
| API        | FastAPI (async), mounted in the same process, JWT auth    |
| Database   | PostgreSQL 16 + PostGIS + pgvector (HNSW semantic search) |
| Queue      | Celery + Redis (worker + nightly beat scheduler)          |
| Search     | Meilisearch + Postgres icontains fallback                 |
| Hybrid     | Reciprocal Rank Fusion (keyword + semantic)               |
| Embeddings | hash (dev) or fastembed ONNX (production)                 |
| Frontend   | Vue 3 + Vite + Pinia + Tailwind CSS 4 + Mapbox GL JS      |
| Mobile     | Android: Kotlin + Jetpack Compose + osmdroid (OSM)        |
| Routing    | OSRM (optional) with haversine straight-line fallback     |

## Features

### ✅ Complete & Tested

- **Search** (3 modes):
  - Keyword: Full-text via Meilisearch (with Postgres fallback)
  - Semantic: pgvector embeddings (384 dims, HNSW index, cosine distance)
  - Hybrid: RRF fusion of both channels
- **POI Management**:
  - Create, view, categorize; denormalized rating/counts
  - Reviews (upsert per user, auto-recompute avg rating)
  - Check-ins with optional comments
  - Similar POI discovery via semantic similarity
- **Route Building**:
  - Interactive map constructor: click to add stops
  - Auto-optimize stop order (nearest-neighbor heuristic)
  - Transport modes: walking, cycling, driving, transit
  - Real OSRM routing (configurable) or straight-line fallback
  - Publish, save, and share routes
- **Social Graph**:
  - Follow/unfollow users
  - Activity feed (check-ins, reviews, published routes from followers)
  - Public user profiles with follower counts
- **Frontend Pages**:
  - **Home** — featured public routes
  - **Search** — hybrid keyword+semantic discovery with debounce
  - **Map** — interactive route builder with live preview
  - **POI Detail** — full reviews, check-ins, similar places
  - **Feed** — merged activity of followed users (with pagination)
  - **Profile** — user bio, followers/following, follow/unfollow
  - **Login** — register and sign in with JWT persistence
- **Android App (MVP)** — native Kotlin + Jetpack Compose (`mobile-android/`):
  - Bottom-nav tabs: Routes, hybrid Search, Map (osmdroid), Feed, Profile
  - Interactive route builder: tap markers to pick stops, server-side order optimization
  - POI detail with reviews, check-ins and semantic "similar places"
  - JWT session persisted in DataStore; design notes in [docs/mobile-app.md](docs/mobile-app.md)

### Infrastructure

- **39 passing tests** (auth, POIs, routes, social, embeddings, search, cache)
- **Celery tasks**: `enrich_poi` (embeddings), `reindex_all_pois` (nightly reindex)
- **Management command**: `reindex_search` for manual Meilisearch rebuild
- **Docker Compose**: db, redis, meilisearch, backend (FastAPI), worker, beat, frontend
- **GitHub Actions CI**: backend tests + lint, frontend build
- **Environment-based degrade**: search, cache, and routing all gracefully degrade when services are down

---

## Getting Started

### 1. Clone & Install

```bash
git clone https://github.com/pritilab/routehub.git
cd routehub
```

### 2. Local Environment

Copy secrets (already generated for the repo, stored locally):

```bash
cp .env.example .env
```

Then add to `.env`:

```bash
# From .env.local (generated at setup, or copy from GitHub Actions secrets)
JWT_SECRET=e72355276964f1812968f0c70656cd958a7c7ae2f7af6693ca2d3489994a14e0
MEILI_MASTER_KEY=8851e96848c7a6818bef0c8eb314b877498bd36260ba1a6df5fbb0940068e002
SECRET_KEY=d82f2880a1a988e3c6e5e2f2d5c1006de0e576a2dfbb477b94fe5ec99e3e6729

# Local dev
BACKEND_PORT=8010          # change if 8000 is in use
EMBEDDING_BACKEND=hash     # or 'fastembed' for real ONNX
CELERY_TASK_ALWAYS_EAGER=0

# Optional: real routing and map rendering
# OSRM_URL=http://osrm:5000
# VITE_MAPBOX_TOKEN=pk.eyJ...
```

### 3. Start Services

```bash
docker compose up --build
```

First run — initialize database:

```bash
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py createsuperuser
```

### 4. Access

- **Frontend**: <http://localhost:5173>
- **API docs**: <http://localhost:8010/api/docs>
- **Django admin**: <http://localhost:8010/admin/>
- **Health**: <http://localhost:8010/api/v1/health>

### 5. Android App (optional)

```bash
cd mobile-android
# point the app at your backend (defaults to emulator loopback http://10.0.2.2:8010/api/v1/)
# edit local.properties: routehub.apiBaseUrl=http://<your-lan-ip>:8010/api/v1/
./gradlew assembleDebug        # APK: app/build/outputs/apk/debug/app-debug.apk
```

Design notes: [docs/mobile-app.md](docs/mobile-app.md).

---

## Development

### Tests

```bash
# Run all tests in Docker
docker compose run --rm backend pytest

# Lint backend
docker compose run --rm backend ruff check .

# Build frontend
docker compose run --rm --no-deps frontend npm run build
```

**Test coverage**: 39 tests covering auth, POIs, routes, social layer, embeddings, search, and caching.
All tests run with `--no-migrations` (tables created directly from models); PostGIS and pgvector
extensions are installed into `template1`, so pytest's test database inherits them automatically.

### Common Tasks

```bash
# Rebuild search index (run inside container or via Celery nightly)
docker compose run --rm backend python manage.py reindex_search

# Create a migration after model changes
docker compose run --rm backend python manage.py makemigrations

# Apply migrations
docker compose run --rm backend python manage.py migrate

# Django shell
docker compose run --rm backend python manage.py shell

# Frontend dev server (already running, hot-reload at :5173)
docker compose logs -f frontend
```

### Architecture

**One backend process, two frameworks:**
- `api/main.py` initializes Django, mounts FastAPI under `/api/*`, and Django ASGI at `/` (admin).
- FastAPI endpoints use Django's async ORM (`aget`, `acreate`, `async for`).
- Services (routing, search, embeddings, caching) live in `services/` — all best-effort with graceful degradation.

**Database:**
- GeoDjango models with PostGIS indexes (GiST for geo queries, HNSW for pgvector).
- Denormalized counters (`rating_avg`, `visit_count`, `save_count`) updated via `F()` expressions.
- Migrations tracked in each app's `migrations/` folder.

**Routing & Search:**
- `services/routing.py`: OSRM when configured, otherwise haversine straight-line fallback.
- `services/search.py`: Meilisearch (best-effort) + Postgres `icontains` fallback, with RRF fusion.
- `services/embeddings.py`: Hash-based (dev) or ONNX fastembed (prod), 384-dimensional vectors.

**Caching:**
- Redis with versioned namespaces — writers bump version counters, readers auto-miss stale entries.
- All cache operations are best-effort; Redis being down never breaks reads.

**Celery:**
- `worker` service: runs `enrich_poi` (compute embeddings) and other tasks.
- `beat` service: nightly reindex of all POIs into Meilisearch (03:00 UTC).
- In tests, `CELERY_TASK_ALWAYS_EAGER=0` keeps tasks async.

---

## Optional: Real Routing (OSRM)

To enable turn-by-turn routing over real streets:

```bash
mkdir osrm-data && cd osrm-data
# Download an OSM extract (example: Netherlands)
curl -O https://download.geofabrik.de/europe/netherlands-latest.osm.pbf
# Preprocess (takes 5–10 minutes)
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-extract -p /opt/foot.lua /data/netherlands-latest.osm.pbf
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-partition /data/netherlands-latest.osrm
docker run -t -v .:/data ghcr.io/project-osrm/osrm-backend osrm-customize /data/netherlands-latest.osrm
mv netherlands-latest.osrm map.osrm
cd ..
```

Then in `.env`:

```bash
OSRM_URL=http://osrm:5000
```

Start with the routing profile:

```bash
docker compose --profile routing up
```

---

## Deployment

### Environment Variables

**Required for production** (auto-generated in GitHub Actions):
- `JWT_SECRET` — 32-byte hex JWT signing key
- `MEILI_MASTER_KEY` — 32-byte hex Meilisearch key
- `SECRET_KEY` — 32-byte hex Django secret

**Optional**:
- `EMBEDDING_BACKEND` — `hash` (dev) or `fastembet` (production, downloads ONNX model ~100MB)
- `OSRM_URL` — if you run a self-hosted routing engine
- `VITE_MAPBOX_TOKEN` — from mapbox.com for interactive maps

### CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push:
- Backend: `pytest` + `ruff check` inside Docker
- Frontend: `npm run build` and lint

All tests must pass before merge.

### Production Notes

- Use managed PostgreSQL (RDS, Supabase, etc.) with PostGIS extension.
- Redis can be managed (ElastiCache) or self-hosted.
- Meilisearch can be self-hosted via Docker or consumed as a service.
- Celery worker and beat should run in separate containers/VMs for reliability.
- Frontend can be static-deployed to S3 + CloudFront after `npm run build`.
- API runs on Gunicorn/uWSGI + reverse proxy (Nginx).

---

## Project Layout

```text
backend/
  config/                  # Django settings, ASGI, Celery beat schedule
  apps/
    accounts/              # User, Follow (social graph)
    businesses/            # Business profiles & subscriptions
    pois/                  # POI with PostGIS point, pgvector embedding
                           # Review, CheckIn models
    routes/                # Route geometry, RoutePoint junctions
                           # RouteCollaborator, SavedRoute
  api/
    routers/               # FastAPI endpoints (auth, pois, routes, users, search, feed)
    schemas/               # Pydantic models (request/response)
    security.py            # JWT token creation/validation
    deps.py                # FastAPI dependencies (auth injection)
    main.py                # App init + middleware
  services/
    routing.py             # OSRM or haversine route computation
    search.py              # Meilisearch + Postgres hybrid search + RRF
    cache.py               # Redis versioned-namespace caching
    embeddings.py          # Hash or fastembed text → vector
  tests/                   # pytest suite (39 tests)
    test_*.py              # Auth, POIs, routes, social, embeddings, search
  manage.py                # Django CLI
  requirements.txt         # Python dependencies

frontend/
  src/
    pages/                 # Vue route views
      HomeView.vue         # Public routes list
      SearchView.vue       # Hybrid search with debounce
      MapView.vue          # Interactive route builder
      PoiDetailView.vue    # Reviews, check-ins, similar places
      FeedView.vue         # Activity feed of followed users
      ProfileView.vue      # User profiles, followers/following
      LoginView.vue        # Auth (register & sign in)
    components/
      PoiCard.vue          # Reusable POI card with similar-places drawer
      MapCanvas.vue        # Mapbox GL JS renderer with route polyline
    stores/
      auth.js              # Pinia auth state (JWT, session restore)
    router/index.js        # Vue Router with auth guards
    api/client.js          # HTTP client for all API routes
    utils/time.js          # Relative time formatting (timeAgo)
  vite.config.js           # Dev server config (polling for Docker on Windows)
  package.json             # Node dependencies

mobile-android/
  app/src/main/java/com/pritilab/routehub/
    data/                  # Retrofit API, DTOs, TokenStore (DataStore), Session
    ui/                    # Compose theme, navigation, screens (7)
  build.gradle.kts         # AGP 9.1, built-in Kotlin, Compose
  local.properties         # SDK path + routehub.apiBaseUrl (git-ignored)

db/
  Dockerfile               # PostGIS + pgvector image
  init.sql                 # Install extensions into template1

docker-compose.yml         # Full stack orchestration
.env.example               # Environment template
.env.local                 # Local secrets (git-ignored)
.github/workflows/ci.yml   # GitHub Actions CI
README.md                  # This file
CLAUDE.md                  # Developer notes
```

---

## Troubleshooting

**Port 8000 in use:**
```bash
BACKEND_PORT=8010 docker compose up
```

**Old modules in frontend dev server:**
```bash
# Vite dev server on Windows/Docker has file-watch issues
# Solution: polling is enabled in vite.config.js, restart container if stuck
docker compose restart frontend
```

**Tests fail with "Event loop is closed":**
```bash
# Async Redis clients are cached per event loop — this is normal in test suites
# Try running tests again; it's usually transient
docker compose run --rm backend pytest
```

**Meilisearch index out of sync:**
```bash
docker compose run --rm backend python manage.py reindex_search
```

**Embeddings not computed:**
- Check Celery worker logs: `docker compose logs worker`
- For tests, set `CELERY_TASK_ALWAYS_EAGER=0` (the default in `.env.example`)

---

## License

MIT — see LICENSE file.

---

**Questions or contributions?** Open an issue or PR in [pritilab/routehub](https://github.com/pritilab/routehub).
