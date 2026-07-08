# RouteHub — API Reference

Base URL: `/api/v1`. Interactive docs: `/api/docs` (OpenAPI). All bodies are
JSON. Coordinates are `{lat, lng}` objects. Timestamps are ISO-8601 UTC.
Lists paginate with `limit`/`offset` query params and return plain arrays.

**Auth**: `Authorization: Bearer <access_token>` (JWT HS256). 🔒 = required,
👤 = optional (enriches the response, e.g. `is_following`).

Errors: FastAPI standard — `{"detail": "message"}` with 4xx/5xx status.

## auth

| Method | Path             | Auth | Description |
|--------|------------------|------|-------------|
| POST   | `/auth/register` | —    | body `{email, username, password, display_name?}` → `UserOut` 201 |
| POST   | `/auth/login`    | —    | body `{email, password}` → `{access_token, refresh_token, token_type}` |
| POST   | `/auth/refresh`  | —    | body `{refresh_token}` → new token pair |
| GET    | `/auth/me`       | 🔒   | current `UserOut` |

`UserOut`: `id, email, username, display_name, avatar_url, bio, role`.

## pois

| Method | Path                  | Auth | Description |
|--------|-----------------------|------|-------------|
| GET    | `/pois`               | —    | filters: `lat`+`lng`+`radius_m` (≤50 km) **or** `bbox=minLng,minLat,maxLng,maxLat`; `city`, `category`; cached in Redis (versioned `pois` namespace) |
| POST   | `/pois`               | 🔒   | `POICreate` → 201; enqueues `enrich_poi` (embedding) and search indexing |
| GET    | `/pois/{id}`          | —    | `POIOut` |
| GET    | `/pois/{id}/similar`  | —    | pgvector cosine neighbors of this POI (`limit` ≤ 50) |
| GET    | `/pois/{id}/reviews`  | —    | list of `ReviewOut` |
| POST   | `/pois/{id}/reviews`  | 🔒   | `{rating: 1..5, text?}` — **upsert** per user; recomputes `rating_avg/count` → 201 |
| POST   | `/pois/{id}/checkin`  | 🔒   | `{comment?}` (≤280) → `CheckInOut` 201; increments `visit_count` |

`POIOut`: `id, title, description, short_description, location{lat,lng},
address, city, country, categories[], photos[], is_official, is_temporary,
rating_avg, rating_count, visit_count, save_count, metadata{}, created_at`.

## search

| Method | Path                    | Auth | Description |
|--------|-------------------------|------|-------------|
| GET    | `/search/pois`          | —    | keyword: Meilisearch, Postgres `icontains` fallback; `q` (≤200) |
| GET    | `/search/pois/semantic` | —    | embedding cosine search; `q` (≤500) |
| GET    | `/search/pois/hybrid`   | —    | RRF fusion of both; `q`, `limit`, `k` (RRF dampening, default 60) |

All return ranked `POIOut[]`.

## routes

| Method | Path                 | Auth | Description |
|--------|----------------------|------|-------------|
| GET    | `/routes`            | 👤   | public routes (+ own when authed), newest first |
| POST   | `/routes`            | 🔒   | `RouteCreate` → 201 (below) |
| GET    | `/routes/{id}`       | 👤   | full `RouteOut`; owners see private routes |
| POST   | `/routes/{id}/save`  | 🔒   | bookmark → 204 (idempotent) |
| DELETE | `/routes/{id}/save`  | 🔒   | remove bookmark → 204 |
| GET    | `/routes/saved/mine` | 🔒   | my bookmarks |

`RouteCreate`: `{title, description?, route_type?, transport_mode?,
theme_tags?, is_public?, optimize_order?, points: [{poi_id,
stay_duration_minutes?, custom_note?}] (min 2)}`.

Server pipeline: fetch POIs → optional nearest-neighbor reordering
(`optimize_order=true`) → per-leg OSRM or haversine geometry → persist route +
points in one transaction.

`RouteOut` adds: `total_distance_meters, estimated_duration_minutes,
difficulty_level, geometry: [{lat,lng}] (polyline), points:
[{poi: POIOut, order_index, stay_duration_minutes, custom_note,
distance_to_next_meters, duration_to_next_minutes}], created_at`.

## users (social)

| Method | Path                          | Auth | Description |
|--------|-------------------------------|------|-------------|
| GET    | `/users/{username}`           | 👤   | `ProfileOut` (`followers_count`, `following_count`, `is_following` when authed) |
| POST   | `/users/{username}/follow`    | 🔒   | → 204 (idempotent; self-follow → 400) |
| DELETE | `/users/{username}/follow`    | 🔒   | → 204 |
| GET    | `/users/{username}/followers` | —    | `PublicUserOut[]` |
| GET    | `/users/{username}/following` | —    | `PublicUserOut[]` |

## feed

| Method | Path    | Auth | Description |
|--------|---------|------|-------------|
| GET    | `/feed` | 🔒   | merged activity of followed users, newest first |

`FeedItemOut`: `{type: "checkin" | "review" | "route_published", created_at,
actor: PublicUserOut, poi?: {id, title, city, location}, route?: {id, title,
transport_mode, theme_tags, total_distance_meters,
estimated_duration_minutes}, comment, rating?, text}`.

Implementation: read-time merge of CheckIn/Review/Route over the `Follow`
graph; each source over-fetched to `offset+limit`, merged by recency.

## misc

| Method | Path      | Description |
|--------|-----------|-------------|
| GET    | `/health` | `{status, db, redis}` liveness/readiness |

## Client notes

- Web SPA client: `frontend/src/api/client.js`. Android client:
  `mobile-android/.../data/RouteHubApi.kt` — DTOs mirror the Pydantic schemas
  field-for-field; change them together.
- 401 on any 🔒 endpoint means the access token expired — refresh or re-login;
  clients drop the stored token (`Session`/Pinia auth store behavior).
