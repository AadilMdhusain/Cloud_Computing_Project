from django.contrib import admin
from .models import Driver

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'current_lat', 'current_lng', 'free_seats', 
                    'is_simulating', 'sim_timestamp', 'matched_station_id')
    list_filter = ('is_simulating',)
    search_fields = ('user_id',)

