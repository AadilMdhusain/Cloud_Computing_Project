from rest_framework import serializers
from .models import Driver
import json


class DriverSerializer(serializers.ModelSerializer):
    route_queue = serializers.SerializerMethodField()
    
    class Meta:
        model = Driver
        fields = ['id', 'user_id', 'current_lat', 'current_lng', 'free_seats', 
                  'route_queue', 'sim_timestamp', 'is_simulating', 
                  'matched_station_id', 'wait_counter']
    
    def get_route_queue(self, obj):
        return obj.route_queue


class CreateDriverSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    free_seats = serializers.IntegerField(default=4)
    route = serializers.ListField(
        child=serializers.DictField(child=serializers.FloatField()),
        required=True
    )
    
    def create(self, validated_data):
        from datetime import datetime
        route = validated_data.pop('route')
        driver = Driver.objects.create(**validated_data)
        driver.route_queue = route
        
        # Set initial position to first coordinate
        if route:
            driver.current_lat = route[0]['lat']
            driver.current_lng = route[0]['lng']
        
        # Initialize sim_timestamp to current time (HH:MM format)
        driver.sim_timestamp = datetime.now().strftime('%H:%M')
        
        driver.save()
        return driver

