# RouteHub — Product & Tech Roadmap

Status date: 2026-07-08. Priorities follow the business plan
([business-plan.md](business-plan.md)): prove B2C engagement in one city, then
sell B2B on top of it.

## ✅ Done (MVP)

Backend (Django+FastAPI, PostGIS, pgvector, Celery), hybrid search (RRF),
route builder with server-side optimization, social layer (follow/check-in/
review/feed), Vue 3 web app (7 pages), native Android app (7 screens), Docker
Compose stack, CI, 39 tests.

## Phase 1 — Launchable beta (4–6 weeks)

Goal: a stranger in Amsterdam can sign up, walk a route, and come back.

- **Product**
  - POI creation from the map (web + Android) with photo upload (S3-compatible
    storage, thumbnailing Celery task)
  - Route detail: map preview on web route page; share links (public slugs)
  - Seed content: 150–300 curated Amsterdam POIs, 20–30 themed routes
    (curator role starts mattering here)
  - Email verification + password reset
- **Tech debt / risk**
  - Rate limiting (per-IP + per-user) on auth and write endpoints
  - HTTPS everywhere; remove `usesCleartextTraffic` from Android release build
  - Real OSRM (walking+cycling profiles, NL extract) in staging and prod
  - Error tracking (Sentry) + structured logging
- **Metrics from day one**: DAU/WAU, routes started/completed, check-ins per
  user, D7 retention. (`completion_count` model field is already there —
  needs a "complete route" client action.)

## Phase 2 — B2B foundation (6–10 weeks)

Goal: first 10 paying venues.

- Business onboarding flow: claim/verify a venue (`Business.verified`),
  business dashboard (views, check-ins, saves, appearance in routes — the
  denormalized counters already collect this)
- Official POI badge + priority in ranking (bounded boost, disclosed)
- Subscription tiers wired to Stripe (`subscription_tier` is modeled);
  free tier = claimed listing, paid = analytics + placement + temporary POIs
  (pop-ups use `is_temporary`/`active_from/until`)
- Curator tooling: multi-day routes UI (`parent_route`/`day_number` exist),
  collaborative editing (RouteCollaborator API + UI)
- iOS: decision point — KMP shared `data/` layer vs. thin native client

## Phase 3 — Engagement & scale (quarter 2)

- Push notifications (FCM): new follower, followee published a route,
  pop-up POI near you
- Personalized recommendations: user embedding = mean of interacted-POI
  vectors → pgvector ANN over routes/POIs (infra already in place)
- Offline mode in Android (route + tiles cache for tourists without data)
- Feed materialization if follow graph grows (see architecture §7)
- Premium routes marketplace (`is_premium`/`premium_price` modeled):
  rev-share with curators — validates the second revenue stream
- Second city playbook (Rotterdam or Utrecht), then first non-EU market test
  (Brazil or India per business plan §6)

## Explicit non-goals for now

- Real-time collaborative editing (CRDT) — invite/roles only
- In-app navigation turn-by-turn — deep-link to OSM/Google for nav
- User-generated events platform — temporary POIs cover the MVP need
- Multi-region infrastructure — single EU region until latency data says
  otherwise
