from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RideRequest
from .serializers import RideRequestSerializer


class RideRequestViewSet(viewsets.ModelViewSet):
    queryset = RideRequest.objects.all()
    serializer_class = RideRequestSerializer
    
    def create(self, request):
        serializer = RideRequestSerializer(data=request.data)
        if serializer.is_valid():
            ride_request = serializer.save()
            return Response({
                'success': True,
                'ride_request_id': ride_request.id,
                'rider_id': ride_request.rider_id,
                'station_id': ride_request.station_id,
                'status': ride_request.status
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': str(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_rider(self, request):
        rider_id = request.query_params.get('rider_id')
        if not rider_id:
            return Response({
                'success': False,
                'message': 'rider_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ride_requests = RideRequest.objects.filter(rider_id=rider_id)
        serializer = RideRequestSerializer(ride_requests, many=True)
        return Response({
            'success': True,
            'rides': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_station(self, request):
        station_id = request.query_params.get('station_id')
        status_filter = request.query_params.get('status', 'LOOKING')
        
        if not station_id:
            return Response({
                'success': False,
                'message': 'station_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ride_requests = RideRequest.objects.filter(
            station_id=station_id,
            status=status_filter
        )
        serializer = RideRequestSerializer(ride_requests, many=True)
        return Response({
            'success': True,
            'rides': serializer.data,
            'count': ride_requests.count()
        })

