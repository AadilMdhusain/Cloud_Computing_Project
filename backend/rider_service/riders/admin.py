from django.contrib import admin
from .models import RideRequest

@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider_id', 'station_id', 'eta', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('rider_id', 'station_id')

