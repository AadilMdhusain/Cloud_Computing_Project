from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationMarkReadSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get all notifications for a user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        notifications = Notification.objects.filter(user_id=user_id)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications for a user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        notifications = Notification.objects.filter(user_id=user_id, is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for a user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        count = Notification.objects.filter(user_id=user_id, is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark notifications as read"""
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.validated_data.get('mark_all'):
            # Mark all notifications for user as read
            updated = Notification.objects.filter(
                user_id=user_id,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
            return Response({'marked_read': updated})
        
        # Mark specific notifications as read
        notification_ids = serializer.validated_data.get('notification_ids', [])
        updated = Notification.objects.filter(
            id__in=notification_ids,
            user_id=user_id,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'marked_read': updated})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Clear all notifications for a user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count, _ = Notification.objects.filter(user_id=user_id).delete()
        return Response({'deleted': deleted_count})

