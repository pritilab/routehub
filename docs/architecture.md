# RouteHub — System Architecture

Status: MVP (July 2026). Companion docs: [data-model.md](data-model.md),
[api.md](api.md), [mobile-app.md](mobile-app.md), [roadmap.md](roadmap.md),
[business-plan.md](business-plan.md).

## 1. Overview

RouteHub is a geo-social platform: users and businesses place points of interest
(POI) on a map; the system assembles optimized routes from selected POIs; a social
layer (follows, check-ins, reviews, feed) drives discovery and retention.

```text
 ┌─────────────┐   ┌──────────────────┐
 │  Vue 3 SPA  │   │ Android (Compose) │        clients
 └──────┬──────┘   └────────┬─────────┘
        │  HTTPS/JSON (JWT) │
        ▼                   ▼
 ┌──────────────────────────────────────┐
 │  Backend process (ASGI)              │
 │  FastAPI  /api/v1/*   (async ORM)    │
 │  Django   /admin, migrations, models │
 └───┬────────┬────────┬────────┬───────┘
     │        │        │        │ best-effort services
     ▼        ▼        ▼        ▼
 PostgreSQL  Redis  Meilisearch OSRM (optional)
 PostGIS      │      (keyword    (street routing;
 pgvector     │       search)     haversine fallback)
              ▼
        Celery worker + beat
        (embeddings, nightly reindex)
```

## 2. One process, two frameworks

`api/main.py` boots Django first (settings, apps, ORM), then mounts:

- **FastAPI** at `/api/*` — all product endpoints, async, Pydantic v2 schemas,
  OpenAPI docs at `/api/docs`.
- **Django ASGI** at `/` — admin UI and anything Django-native.

Why: GeoDjango is the best Python ORM for PostGIS (spatial fields, migrations,
admin for content ops), while FastAPI gives async request handling, first-class
OpenAPI and Pydantic validation. One process keeps deployment trivial at MVP
stage; the split into separate services is a scaling decision, not a rewrite
(see §7).

Rules that keep this hybrid sane (enforced in `AGENTS.md`):

- Endpoints use Django's async ORM (`aget`, `acreate`, `async for`).
- Multi-write transactions run in a sync function via `run_in_threadpool`
  (Django transactions are thread-bound).
- Coordinates: JSON is `{lat, lng}`; PostGIS is `(lng, lat)` — conversion happens
  only in schema `from_model` helpers.

## 3. Services layer — graceful degradation

All external infra sits behind `backend/services/` and is **best-effort**: the
product must keep working (possibly slower/simpler) when any of it is down.

| Service      | Module          | Degradation path                                  |
|--------------|-----------------|---------------------------------------------------|
| Redis cache  | `cache.py`      | cache miss → query DB; failures swallowed         |
| Meilisearch  | `search.py`     | keyword search falls back to Postgres `icontains` |
| OSRM         | `routing.py`    | falls back to haversine straight lines            |
| Embeddings   | `embeddings.py` | `hash` backend needs no model download            |

Caching uses **versioned namespaces**: readers key entries by
`{namespace}:{version}:{params}`; writers `bump_version("pois")` instead of
enumerating keys to invalidate. Async Redis clients are cached **per event
loop** (module-level singletons break under multiple loops).

## 4. Route computation

`services/routing.py` → `compute_route(points, transport_mode)`:

1. **Order optimization** (`optimize_order=True`, route_type `auto`):
   nearest-neighbor heuristic over haversine distances. O(n²), fine for n ≤ ~50
   stops; swap for OR-Tools TSP when multi-day routes grow.
2. **Leg geometry**: OSRM `route` API per leg when `OSRM_URL` is set (real
   street polylines, durations by profile); otherwise straight lines +
   speed-table estimates per transport mode.
3. Result is persisted denormalized on `Route` (geometry LINESTRING,
   total_distance_meters, estimated_duration_minutes) and per-leg on
   `RoutePoint` (distance/duration to next).

## 5. Search — two channels fused

- **Keyword**: Meilisearch index of POI documents (title, descriptions,
  categories, city), kept fresh by write-path best-effort indexing + nightly
  full reindex (Celery beat, 03:00 UTC). Postgres fallback when Meili is down.
- **Semantic**: 384-dim embeddings in pgvector, HNSW index, cosine distance.
  Embeddings are computed off the request path by the `enrich_poi` Celery task.
  Backends: `hash` (dev/test, deterministic token-overlap) or `fastembed`
  (ONNX BAAI/bge-small-en-v1.5).
- **Hybrid** endpoint merges both with Reciprocal Rank Fusion:
  `score(d) = Σ 1/(k + rank_i(d))`, tunable `k` (default 60). Both-channel hits
  outrank single-channel leaders.

The same embedding space powers **"similar POIs"** (nearest neighbors of a
POI's own vector), used for discovery on the POI page and mobile app.

## 6. Async work — Celery

- `worker`: `enrich_poi` (embedding on create/update), future: photo
  processing, notifications.
- `beat`: nightly `reindex_all_pois` into Meilisearch (self-heals index drift;
  raises → autoretry with backoff).
- Task code is sync (Celery-native); it calls `*_sync` service variants that
  raise, while request-path variants never raise.

## 7. Scaling path (when needed, in order)

1. **Read replicas + PgBouncer** — geo/list queries are read-heavy.
2. **Split API from admin** — same image, two deployments; stateless API scales
   horizontally behind a load balancer (JWT, no server sessions).
3. **Feed materialization** — current feed is a read-time merge over three
   tables filtered by `Follow`; at ~10⁵ follows introduce a fan-out-on-write
   feed table (the read-time version stays as fallback logic).
4. **Tile/route cache** — OSRM responses and popular route geometries in Redis.
5. **Search sharding** — Meilisearch per-region indexes align with the
   city-centric product; pgvector HNSW handles ~10⁷ POIs per node comfortably.

## 8. Security posture (MVP)

- JWT HS256, short-lived access + refresh tokens; passwords via Django's
  PBKDF2 hasher.
- Role field on User (`user | business | curator | admin`) — enforcement today
  is thin (ownership checks); role-gated endpoints arrive with the B2B panel.
- Secrets only via environment (`.env` git-ignored); CI secrets in GitHub
  Actions.
- Known MVP debts: no rate limiting, no email verification, mobile dev build
  allows cleartext HTTP. Tracked in [roadmap.md](roadmap.md).
