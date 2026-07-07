import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from pgvector.django import HnswIndex, VectorField


class PointOfInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pois"
    )
    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pois",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=280, blank=True)
    location = gis_models.PointField(srid=4326)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    categories = ArrayField(models.CharField(max_length=64), default=list, blank=True)
    photos = ArrayField(models.URLField(), default=list, blank=True)
    is_official = models.BooleanField(default=False)
    is_temporary = models.BooleanField(default=False)
    active_from = models.DateTimeField(null=True, blank=True)
    active_until = models.DateTimeField(null=True, blank=True)
    rating_avg = models.FloatField(default=0.0)
    rating_count = models.PositiveIntegerField(default=0)
    visit_count = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    # Semantic search embedding (description + categories), filled by a Celery task.
    embedding = VectorField(dimensions=384, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "points_of_interest"
        indexes = [
            models.Index(fields=["city"]),
            GinIndex(fields=["categories"]),
            HnswIndex(
                name="poi_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return self.title


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poi = models.ForeignKey(PointOfInterest, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "poi_reviews"
        constraints = [
            models.UniqueConstraint(fields=["poi", "user"], name="uq_review_per_user_poi"),
        ]


class CheckIn(models.Model):
    """A user marking presence at a POI — feeds visit_count and the social feed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poi = models.ForeignKey(PointOfInterest, on_delete=models.CASCADE, related_name="checkins")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="checkins"
    )
    comment = models.CharField(max_length=280, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "poi_checkins"
        indexes = [models.Index(fields=["user", "-created_at"])]
