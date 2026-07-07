from django.contrib import admin

from .models import Route, RouteCollaborator, RoutePoint, SavedRoute

admin.site.register(Route)
admin.site.register(RoutePoint)
admin.site.register(RouteCollaborator)
admin.site.register(SavedRoute)
