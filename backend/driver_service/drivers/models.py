from django.db import models
import json


class Driver(models.Model):
    user_id = models.IntegerField(unique=True)
    current_lat = models.FloatField(default=0.0)
    current_lng = models.FloatField(default=0.0)
    free_seats = models.IntegerField(default=4)
    
    # Route queue stored as JSON array of coordinates
    # Format: [{"lat": 12.34, "lng": 56.78}, ...]
    route_queue_json = models.TextField(default='[]')
    
    # Simulation state
    sim_timestamp = models.CharField(max_length=10, default='10:00')  # HH:MM format
    is_simulating = models.BooleanField(default=False)
    
    # Matched station info
    matched_station_id = models.IntegerField(null=True, blank=True)
    wait_counter = models.IntegerField(default=0)  # Counter for waiting at station
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['is_simulating']),
        ]
    
    @property
    def route_queue(self):
        """Get route queue as Python list"""
        try:
            return json.loads(self.route_queue_json)
        except:
            return []
    
    @route_queue.setter
    def route_queue(self, value):
        """Set route queue from Python list"""
        self.route_queue_json = json.dumps(value)
    
    def peek_route(self):
        """Get the first coordinate in route without removing it"""
        queue = self.route_queue
        return queue[0] if queue else None
    
    def pop_route(self):
        """Remove and return the first coordinate from route"""
        queue = self.route_queue
        if queue:
            coord = queue.pop(0)
            self.route_queue = queue
            self.save()
            return coord
        return None
    
    def push_front_route(self, coord):
        """Add coordinate to the front of the route queue"""
        queue = self.route_queue
        queue.insert(0, coord)
        self.route_queue = queue
        self.save()
    
    def __str__(self):
        return f"Driver {self.user_id} - ({self.current_lat}, {self.current_lng})"

