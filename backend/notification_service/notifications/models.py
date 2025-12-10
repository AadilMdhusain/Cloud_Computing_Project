from django.db import models


class Notification(models.Model):
    """
    In-App Notification Model
    """
    NOTIFICATION_TYPES = [
        ('MATCH_FOUND', 'Match Found'),
        ('TRIP_SCHEDULED', 'Trip Scheduled'),
        ('TRIP_STARTED', 'Trip Started'),
        ('TRIP_COMPLETED', 'Trip Completed'),
        ('TRIP_CANCELLED', 'Trip Cancelled'),
        ('DRIVER_NEARBY', 'Driver Nearby'),
        ('SYSTEM', 'System Notification'),
    ]
    
    # User who receives the notification
    user_id = models.IntegerField()
    
    # Notification content
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')
    
    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related entities (optional)
    related_trip_id = models.IntegerField(null=True, blank=True)
    related_match_id = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for User {self.user_id}: {self.notification_type}"

