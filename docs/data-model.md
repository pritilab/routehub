# RouteHub — Data Model

Source of truth: `backend/apps/*/models.py`. All PKs are UUIDv4. All tables have
`created_at`; mutable ones also `updated_at`. SRID 4326 everywhere.

```text
User ──< Follow >── User            (social graph, no self-follow)
User ──< Business                   (B2B profile, subscription tier)
User ──< PointOfInterest >── Business (optional official link)
POI  ──< Review (1 per user/POI)    POI ──< CheckIn
User ──< Route ──< RoutePoint >── POI
Route ──< SavedRoute >── User       Route ──< RouteCollaborator >── User
Route ──< Route (parent_route)      (multi-day: day routes under a parent)
```

## accounts

**User** (`users`) — extends `AbstractUser`; login by **email**
(`USERNAME_FIELD`), unique. `display_name`, `avatar_url`, `bio`,
`role` ∈ `user | business | curator | admin`, `location_default` (Point,
nullable — home area for defaults), `last_active_at`.

**Follow** (`follows`) — `follower → followee`. Unique pair, DB-level
`CHECK (follower != followee)`.

## businesses

**Business** (`businesses`) — B2B venue profile owned by a User.
`category` ∈ restaurant/museum/shop/hotel/event_venue/other;
`subscription_tier` ∈ **free/basic/premium/enterprise** (monetization anchor);
`verified` + `verification_date` (manual verification flow, admin-driven for
now).

## pois

**PointOfInterest** (`points_of_interest`) — the core entity.

- Authorship: `created_by` (User), optional `business` (SET_NULL) — an
  official venue POI (`is_official=True`).
- Content: `title`, `description`, `short_description` (≤280),
  `categories` text[], `photos` url[], free-form `metadata` JSONB.
- Geo: `location` Point + address/city/country/postal_code.
- Temporality: `is_temporary`, `active_from/until` — pop-ups, festival stands.
- Denormalized counters: `rating_avg`, `rating_count` (recomputed on review
  upsert), `visit_count` (check-in `F()` increment), `save_count`.
- `embedding` vector(384), nullable — filled asynchronously by Celery.

Indexes: GiST on `location` (implicit for PointField), B-tree on `city`,
GIN on `categories`, **HNSW** `poi_embedding_hnsw`
(m=16, ef_construction=64, `vector_cosine_ops` — must match the
`CosineDistance` used in queries).

**Review** (`poi_reviews`) — rating 1–5 + text; **unique (poi, user)** —
endpoint upserts and recomputes the POI aggregate.

**CheckIn** (`poi_checkins`) — presence mark with optional ≤280 comment;
indexed `(user, -created_at)` for the feed merge.

## routes

**Route** (`routes`) —

- `route_type` ∈ auto/semi_auto/manual (auto = server ordered the stops).
- `transport_mode` ∈ walking/cycling/driving/transit/mixed.
- Computed denorm: `geometry` LINESTRING, `bounds` Polygon,
  `total_distance_meters`, `estimated_duration_minutes`.
- Product flags: `is_public` (+`published_at`, indexed together),
  `is_collaborative`, `is_premium` + `premium_price` (paid curated routes —
  modeled, not yet sold), `difficulty_level`, `theme_tags` text[],
  `cover_image_url`.
- Multi-day: `parent_route` self-FK + `day_number` — day routes are children
  of an umbrella route.
- Counters: `view_count`, `save_count`, `completion_count`.

**RoutePoint** (`route_points`) — ordered junction Route↔POI. Unique
`(route, order_index)`, default ordering by `order_index`. Per-leg denorm:
`transport_to_next`, `distance_to_next_meters`, `duration_to_next_minutes`;
per-stop `stay_duration_minutes`, `custom_note`.

**RouteCollaborator** (`route_collaborators`) — editor/viewer invite with
`invited_at`/`accepted_at`; unique (route, user). API surface post-MVP.

**SavedRoute** (`saved_routes`) — bookmark; unique (route, user).

## Conventions

- Counters update via `F()` expressions or full aggregate recompute in the
  endpoint owning the write — never read-modify-write in Python.
- New Django apps live in `apps/`, registered as `apps.<name>`.
- Tests run `--no-migrations`; the db image installs postgis/vector/pg_trgm
  into `template1` so ephemeral test DBs inherit extensions.
