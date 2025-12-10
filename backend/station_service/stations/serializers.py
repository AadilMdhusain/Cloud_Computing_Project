from rest_framework import serializers
from .models import Station


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ['id', 'name', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['created_at']

