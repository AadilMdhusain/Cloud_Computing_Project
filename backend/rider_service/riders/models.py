from django.db import models


class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('LOOKING', 'Looking for Driver'),
        ('MATCHED', 'Matched with Driver'),
        ('COMPLETED', 'Ride Completed'),
        ('CANCELLED', 'Ride Cancelled'),
    ]
    
    rider_id = models.IntegerField()
    station_id = models.IntegerField()
    eta = models.CharField(max_length=10)  # Format: "HH:MM"
    destination_lat = models.FloatField()
    destination_lng = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='LOOKING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['station_id', 'status']),
            models.Index(fields=['rider_id']),
        ]
    
    def __str__(self):
        return f"Rider {self.rider_id} - Station {self.station_id} - ETA {self.eta} ({self.status})"

