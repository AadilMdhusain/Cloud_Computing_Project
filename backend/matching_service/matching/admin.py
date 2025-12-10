from django.contrib import admin
from .models import Match

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider_id', 'driver_id', 'station_id', 'match_timestamp', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('rider_id', 'driver_id', 'station_id')

