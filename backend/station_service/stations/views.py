from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Station
from .serializers import StationSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    
    def create(self, request):
        serializer = StationSerializer(data=request.data)
        if serializer.is_valid():
            station = serializer.save()
            return Response({
                'success': True,
                'station_id': station.id,
                'name': station.name,
                'latitude': station.latitude,
                'longitude': station.longitude
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': str(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        stations = self.get_queryset()
        serializer = StationSerializer(stations, many=True)
        return Response({
            'success': True,
            'stations': serializer.data,
            'total': stations.count()
        })

