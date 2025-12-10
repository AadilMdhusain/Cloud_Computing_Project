from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    ROLE_CHOICES = [
        ('RIDER', 'Rider'),
        ('DRIVER', 'Driver'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

