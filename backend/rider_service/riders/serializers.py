from rest_framework import serializers
from .models import RideRequest


class RideRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideRequest
        fields = ['id', 'rider_id', 'station_id', 'eta', 'destination_lat', 
                  'destination_lng', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

