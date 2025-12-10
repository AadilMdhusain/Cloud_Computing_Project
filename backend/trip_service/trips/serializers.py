from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating trips from matches"""
    class Meta:
        model = Trip
        fields = ['match_id', 'rider_id', 'driver_id', 'pickup_station_id', 
                  'destination_lat', 'destination_lng']


class TripStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating trip status"""
    status = serializers.ChoiceField(choices=Trip.STATUS_CHOICES)

