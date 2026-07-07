from django.contrib import admin

from .models import CheckIn, PointOfInterest, Review

admin.site.register(PointOfInterest)
admin.site.register(Review)
admin.site.register(CheckIn)
