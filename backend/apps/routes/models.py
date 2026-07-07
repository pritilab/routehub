import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models


class TransportMode(models.TextChoices):
    WALKING = "walking"
    CYCLING = "cycling"
    DRIVING = "driving"
    TRANSIT = "transit"
    MIXED = "mixed"


class Route(models.Model):
    class RouteType(models.TextChoices):
        AUTO = "auto"
        SEMI_AUTO = "semi_auto"
        MANUAL = "manual"

    class Difficulty(models.TextChoices):
        EASY = "easy"
        MODERATE = "moderate"
        HARD = "hard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    route_type = models.CharField(
        max_length=16, choices=RouteType.choices, default=RouteType.MANUAL
    )
    transport_mode = models.CharField(
        max_length=16, choices=TransportMode.choices, default=TransportMode.WALKING
    )
    theme_tags = ArrayField(models.CharField(max_length=64), default=list, blank=True)
    total_distance_meters = models.PositiveIntegerField(default=0)
    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    difficulty_level = models.CharField(
        max_length=16, choices=Difficulty.choices, default=Difficulty.EASY
    )
    is_public = models.BooleanField(default=False)
    is_collaborative = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    geometry = gis_models.LineStringField(srid=4326, null=True, blank=True)
    bounds = gis_models.PolygonField(srid=4326, null=True, blank=True)
    day_number = models.PositiveSmallIntegerField(default=1)
    parent_route = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="days"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    completion_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "routes"
        indexes = [models.Index(fields=["is_public", "-published_at"])]

    def __str__(self):
        return self.title


class RoutePoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="points")
    poi = models.ForeignKey(
        "pois.PointOfInterest", on_delete=models.CASCADE, related_name="route_points"
    )
    order_index = models.PositiveIntegerField()
    stay_duration_minutes = models.PositiveIntegerField(default=0)
    custom_note = models.TextField(blank=True)
    transport_to_next = models.CharField(
        max_length=16, choices=TransportMode.choices, default=TransportMode.WALKING
    )
    distance_to_next_meters = models.PositiveIntegerField(default=0)
    duration_to_next_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "route_points"
        ordering = ["order_index"]
        constraints = [
            models.UniqueConstraint(fields=["route", "order_index"], name="uq_route_order"),
        ]


class RouteCollaborator(models.Model):
    class CollabRole(models.TextChoices):
        EDITOR = "editor"
        VIEWER = "viewer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="collaborators")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="route_collaborations"
    )
    role = models.CharField(max_length=16, choices=CollabRole.choices, default=CollabRole.EDITOR)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "route_collaborators"
        constraints = [
            models.UniqueConstraint(fields=["route", "user"], name="uq_route_collaborator"),
        ]


class SavedRoute(models.Model):
    """Bookmark: a user saving someone's route to their library."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="saves")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_routes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_routes"
        constraints = [
            models.UniqueConstraint(fields=["route", "user"], name="uq_saved_route"),
        ]
