from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Match
from .serializers import MatchSerializer
import requests
import os


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a match and automatically create a trip"""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            match_data = response.data
            # Create trip automatically
            self._create_trip_for_match(match_data)
        
        return response
    
    @action(detail=False, methods=['get'])
    def by_rider(self, request):
        rider_id = request.query_params.get('rider_id')
        if not rider_id:
            return Response({
                'success': False,
                'message': 'rider_id is required'
            }, status=400)
        
        matches = Match.objects.filter(rider_id=rider_id)
        serializer = MatchSerializer(matches, many=True)
        return Response({
            'success': True,
            'matches': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_driver(self, request):
        driver_id = request.query_params.get('driver_id')
        if not driver_id:
            return Response({
                'success': False,
                'message': 'driver_id is required'
            }, status=400)
        
        matches = Match.objects.filter(driver_id=driver_id)
        serializer = MatchSerializer(matches, many=True)
        return Response({
            'success': True,
            'matches': serializer.data
        })
    
    def _create_trip_for_match(self, match_data):
        """Create a trip in Trip Service when match is created"""
        try:
            trip_host = os.environ.get('TRIP_SERVICE_HOST', 'localhost')
            trip_port = os.environ.get('TRIP_SERVICE_PORT', '8006')
            url = f"http://{trip_host}:{trip_port}/api/trips/"
            
            trip_payload = {
                'match_id': match_data['id'],
                'rider_id': match_data['rider_id'],
                'driver_id': match_data['driver_id'],
                'pickup_station_id': match_data.get('pickup_station_id', 1),
                'destination_lat': match_data.get('destination_lat', 0.0),
                'destination_lng': match_data.get('destination_lng', 0.0)
            }
            
            response = requests.post(url, json=trip_payload, timeout=5)
            if response.status_code == 201:
                print(f"✅ Trip created for match {match_data['id']}")
            else:
                print(f"⚠️ Failed to create trip: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating trip: {e}")

