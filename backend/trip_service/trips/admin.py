from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'rider_id', 'driver_id', 'status', 'scheduled_at', 'started_at', 'completed_at']
    list_filter = ['status', 'scheduled_at']
    search_fields = ['rider_id', 'driver_id', 'match_id']

