from django.db import models
from django.conf import settings

class Ride(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('STARTED', 'Started'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rides_as_rider')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides_as_driver')
    
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_address = models.TextField()
    
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # in kilometers
    duration = models.IntegerField(null=True, blank=True)  # in minutes
    
    rider_rating = models.IntegerField(null=True, blank=True)
    driver_rating = models.IntegerField(null=True, blank=True)
    
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ride {self.id} - {self.status}"

class RideLocation(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Location update for ride {self.ride.id} at {self.timestamp}"
