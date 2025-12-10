from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Driver
from .serializers import DriverSerializer, CreateDriverSerializer


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    
    def create(self, request):
        serializer = CreateDriverSerializer(data=request.data)
        if serializer.is_valid():
            driver = serializer.save()
            return Response({
                'success': True,
                'driver_id': driver.id,
                'user_id': driver.user_id,
                'current_lat': driver.current_lat,
                'current_lng': driver.current_lng,
                'route_queue': driver.route_queue
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': str(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        try:
            driver = Driver.objects.get(pk=pk)
            serializer = DriverSerializer(driver)
            return Response({
                'success': True,
                'driver': serializer.data
            })
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Driver not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'message': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            driver = Driver.objects.get(user_id=user_id)
            serializer = DriverSerializer(driver)
            return Response({
                'success': True,
                'driver': serializer.data
            })
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Driver not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def start_simulation(self, request, pk=None):
        try:
            driver = Driver.objects.get(pk=pk)
            driver.is_simulating = True
            driver.save()
            return Response({
                'success': True,
                'message': 'Simulation started'
            })
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Driver not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def stop_simulation(self, request, pk=None):
        try:
            driver = Driver.objects.get(pk=pk)
            driver.is_simulating = False
            driver.save()
            return Response({
                'success': True,
                'message': 'Simulation stopped'
            })
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Driver not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def active_drivers(self, request):
        drivers = Driver.objects.filter(is_simulating=True)
        serializer = DriverSerializer(drivers, many=True)
        return Response({
            'success': True,
            'drivers': serializer.data,
            'count': drivers.count()
        })

