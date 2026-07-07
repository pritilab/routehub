import uuid

from django.conf import settings
from django.db import models


class Business(models.Model):
    class Category(models.TextChoices):
        RESTAURANT = "restaurant"
        MUSEUM = "museum"
        SHOP = "shop"
        HOTEL = "hotel"
        EVENT_VENUE = "event_venue"
        OTHER = "other"

    class SubscriptionTier(models.TextChoices):
        FREE = "free"
        BASIC = "basic"
        PREMIUM = "premium"
        ENTERPRISE = "enterprise"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="businesses"
    )
    business_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
    subscription_tier = models.CharField(
        max_length=16, choices=SubscriptionTier.choices, default=SubscriptionTier.FREE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "businesses"
        verbose_name_plural = "businesses"

    def __str__(self):
        return self.business_name
