from django.db import models


class Trip(models.Model):
    """
    Trip Model - Manages trip lifecycle
    States: SCHEDULED -> ACTIVE -> COMPLETED/CANCELLED
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Link to match
    match_id = models.IntegerField()
    
    # Participants
    rider_id = models.IntegerField()
    driver_id = models.IntegerField()
    
    # Trip details
    pickup_station_id = models.IntegerField()
    destination_lat = models.FloatField()
    destination_lng = models.FloatField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Timestamps
    scheduled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Events
    pickup_time = models.DateTimeField(null=True, blank=True)
    dropoff_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Trip {self.id} - {self.status} (Rider: {self.rider_id}, Driver: {self.driver_id})"

