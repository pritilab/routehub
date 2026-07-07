import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "user"
        BUSINESS = "business"
        CURATOR = "curator"
        ADMIN = "admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.USER)
    location_default = gis_models.PointField(srid=4326, null=True, blank=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.display_name or self.username


class Follow(models.Model):
    """Social graph: follower subscribes to another user's routes and activity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "follows"
        constraints = [
            models.UniqueConstraint(fields=["follower", "followee"], name="uq_follow_pair"),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("followee")), name="ck_no_self_follow"
            ),
        ]
