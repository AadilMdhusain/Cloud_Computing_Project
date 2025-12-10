from rest_framework import serializers
from .models import Match


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['id', 'rider_id', 'driver_id', 'station_id', 'match_timestamp', 'status', 'created_at']
        read_only_fields = ['created_at']

