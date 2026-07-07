"""Route computation: OSRM when configured, straight-line fallback otherwise.

Coordinates are (lng, lat) tuples throughout, matching GeoJSON/PostGIS order.
"""

import math
from dataclasses import dataclass

import httpx
from django.conf import settings

# Rough average speeds for the straight-line fallback, in meters/minute.
FALLBACK_SPEED = {
    "walking": 80,
    "cycling": 250,
    "driving": 600,
    "transit": 400,
    "mixed": 100,
}

OSRM_PROFILE = {
    "walking": "foot",
    "cycling": "bike",
    "driving": "car",
    "transit": "foot",  # OSRM has no transit; approximate with foot
    "mixed": "foot",
}


@dataclass
class Leg:
    distance_m: int
    duration_min: int


@dataclass
class ComputedRoute:
    geometry: list[tuple[float, float]]  # (lng, lat)
    legs: list[Leg]  # len == stops - 1

    @property
    def total_distance_m(self) -> int:
        return sum(leg.distance_m for leg in self.legs)

    @property
    def total_duration_min(self) -> int:
        return sum(leg.duration_min for leg in self.legs)


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lng1, lat1, lng2, lat2 = map(math.radians, (*a, *b))
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6_371_000 * 2 * math.asin(math.sqrt(h))


def optimize_order(coords: list[tuple[float, float]]) -> list[int]:
    """Nearest-neighbor heuristic keeping the first stop fixed. Returns index order."""
    if len(coords) <= 2:
        return list(range(len(coords)))
    remaining = set(range(1, len(coords)))
    order = [0]
    while remaining:
        last = coords[order[-1]]
        nearest = min(remaining, key=lambda i: haversine_m(last, coords[i]))
        order.append(nearest)
        remaining.remove(nearest)
    return order


async def compute_route(
    coords: list[tuple[float, float]], transport_mode: str = "walking"
) -> ComputedRoute:
    if settings.OSRM_URL:
        try:
            return await _osrm_route(coords, transport_mode)
        except (httpx.HTTPError, KeyError, ValueError):
            pass  # OSRM down or bad response -> degrade to straight lines
    return _straight_line_route(coords, transport_mode)


async def _osrm_route(
    coords: list[tuple[float, float]], transport_mode: str
) -> ComputedRoute:
    profile = OSRM_PROFILE.get(transport_mode, "foot")
    coord_str = ";".join(f"{lng},{lat}" for lng, lat in coords)
    url = f"{settings.OSRM_URL}/route/v1/{profile}/{coord_str}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"overview": "full", "geometries": "geojson"})
        resp.raise_for_status()
        data = resp.json()
    route = data["routes"][0]
    geometry = [(lng, lat) for lng, lat in route["geometry"]["coordinates"]]
    legs = [
        Leg(distance_m=round(leg["distance"]), duration_min=round(leg["duration"] / 60))
        for leg in route["legs"]
    ]
    return ComputedRoute(geometry=geometry, legs=legs)


def _straight_line_route(
    coords: list[tuple[float, float]], transport_mode: str
) -> ComputedRoute:
    speed = FALLBACK_SPEED.get(transport_mode, 80)
    legs = []
    for a, b in zip(coords, coords[1:], strict=False):
        dist = haversine_m(a, b)
        legs.append(Leg(distance_m=round(dist), duration_min=round(dist / speed)))
    return ComputedRoute(geometry=list(coords), legs=legs)
