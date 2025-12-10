from django.db import models


class Match(models.Model):
    rider_id = models.IntegerField()
    driver_id = models.IntegerField()
    station_id = models.IntegerField()
    match_timestamp = models.CharField(max_length=10)  # Simulation time HH:MM
    status = models.CharField(max_length=20, default='ACTIVE')  # ACTIVE, COMPLETED, CANCELLED
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['rider_id']),
            models.Index(fields=['driver_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Match: Rider {self.rider_id} <-> Driver {self.driver_id} at Station {self.station_id}"

