from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Trip
from .serializers import TripSerializer, TripCreateSerializer, TripStatusUpdateSerializer
import requests
import os


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TripCreateSerializer
        return TripSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a trip from a match"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip = serializer.save(status='SCHEDULED')
        
        # Send notification
        self._send_notification(
            trip.rider_id,
            f"Trip scheduled! Driver is on the way to pick you up.",
            'TRIP_SCHEDULED'
        )
        self._send_notification(
            trip.driver_id,
            f"New trip scheduled! Please pick up rider at station.",
            'TRIP_SCHEDULED'
        )
        
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a trip (driver picks up rider)"""
        trip = self.get_object()
        if trip.status != 'SCHEDULED':
            return Response(
                {'error': 'Trip must be in SCHEDULED state to start'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trip.status = 'ACTIVE'
        trip.started_at = timezone.now()
        trip.pickup_time = timezone.now()
        trip.save()
        
        # Send notification
        self._send_notification(
            trip.rider_id,
            f"Trip started! You're on your way.",
            'TRIP_STARTED'
        )
        
        return Response(TripSerializer(trip).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a trip (rider dropped off)"""
        trip = self.get_object()
        if trip.status not in ['ACTIVE', 'SCHEDULED']:
            return Response(
                {'error': f'Trip must be in ACTIVE or SCHEDULED state to complete (current: {trip.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If completing a SCHEDULED trip directly (edge case), mark start times too
        if trip.status == 'SCHEDULED':
            trip.started_at = timezone.now()
            trip.pickup_time = timezone.now()
        
        trip.status = 'COMPLETED'
        trip.completed_at = timezone.now()
        trip.dropoff_time = timezone.now()
        trip.save()
        
        # Update match status to COMPLETED
        self._update_match_status(trip.match_id, 'COMPLETED')
        
        # Reset driver status to make them available again
        self._reset_driver(trip.driver_id)
        
        # Send notification
        self._send_notification(
            trip.rider_id,
            f"Trip completed! Thanks for riding with us.",
            'TRIP_COMPLETED'
        )
        self._send_notification(
            trip.driver_id,
            f"Trip completed! You can accept new rides now.",
            'TRIP_COMPLETED'
        )
        
        return Response(TripSerializer(trip).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a trip"""
        trip = self.get_object()
        if trip.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled trip'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trip.status = 'CANCELLED'
        trip.cancelled_at = timezone.now()
        trip.save()
        
        # Send notification
        self._send_notification(
            trip.rider_id,
            f"Trip cancelled.",
            'TRIP_CANCELLED'
        )
        self._send_notification(
            trip.driver_id,
            f"Trip cancelled by rider.",
            'TRIP_CANCELLED'
        )
        
        return Response(TripSerializer(trip).data)
    
    @action(detail=False, methods=['get'])
    def by_rider(self, request):
        """Get trips for a rider"""
        rider_id = request.query_params.get('rider_id')
        if not rider_id:
            return Response({'error': 'rider_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        trips = Trip.objects.filter(rider_id=rider_id)
        serializer = self.get_serializer(trips, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_driver(self, request):
        """Get trips for a driver"""
        driver_id = request.query_params.get('driver_id')
        if not driver_id:
            return Response({'error': 'driver_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        trips = Trip.objects.filter(driver_id=driver_id)
        serializer = self.get_serializer(trips, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_trips(self, request):
        """Get all active trips"""
        trips = Trip.objects.filter(status='ACTIVE')
        serializer = self.get_serializer(trips, many=True)
        return Response(serializer.data)
    
    def _reset_driver(self, driver_id):
        """Reset driver status after trip completion"""
        try:
            driver_host = os.environ.get('DRIVER_SERVICE_HOST', 'localhost')
            driver_port = os.environ.get('DRIVER_SERVICE_PORT', '8004')
            url = f"http://{driver_host}:{driver_port}/api/drivers/{driver_id}/"
            
            # Get current driver data
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                driver_data = response.json()
                # Reset matched_station_id to make driver available
                driver_data['matched_station_id'] = None
                requests.patch(url, json={'matched_station_id': None}, timeout=2)
                print(f"✅ Driver {driver_id} reset and available for new matches")
        except Exception as e:
            print(f"⚠️ Failed to reset driver: {e}")
    
    def _update_match_status(self, match_id, new_status):
        """Update match status in Matching Service"""
        try:
            matching_host = os.environ.get('MATCHING_SERVICE_HOST', 'localhost')
            matching_port = os.environ.get('MATCHING_SERVICE_PORT', '8005')
            url = f"http://{matching_host}:{matching_port}/api/matches/{match_id}/"
            
            requests.patch(url, json={'status': new_status}, timeout=2)
            print(f"✅ Match {match_id} status updated to {new_status}")
        except Exception as e:
            print(f"⚠️ Failed to update match status: {e}")
    
    def _send_notification(self, user_id, message, notification_type):
        """Send notification to notification service"""
        try:
            notification_host = os.environ.get('NOTIFICATION_SERVICE_HOST', 'localhost')
            notification_port = os.environ.get('NOTIFICATION_SERVICE_PORT', '8007')
            url = f"http://{notification_host}:{notification_port}/api/notifications/"
            
            data = {
                'user_id': user_id,
                'message': message,
                'notification_type': notification_type
            }
            
            requests.post(url, json=data, timeout=2)
        except Exception as e:
            print(f"Failed to send notification: {e}")

