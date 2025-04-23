from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('RIDER', 'Rider'),
        ('DRIVER', 'Driver'),
        ('ADMIN', 'Admin'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='RIDER')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_rider(self):
        return self.role == 'RIDER'
    
    def is_driver(self):
        return self.role == 'DRIVER'
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def get_initials(self):
        """Return user's initials for display when no profile picture exists"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return f"{self.first_name[0]}".upper()
        elif self.username:
            return f"{self.username[0]}".upper()
        return "?"

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50)
    license_number = models.CharField(max_length=50)
    license_document = models.FileField(upload_to='documents/licenses/')
    insurance_document = models.FileField(upload_to='documents/insurance/')
    is_available = models.BooleanField(default=False)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Driver Profile"

class RiderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')
    home_address = models.TextField(blank=True)
    work_address = models.TextField(blank=True)
    default_payment_method = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Rider Profile"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('RIDE_REQUEST', 'Ride Request'),
        ('RIDE_ACCEPTED', 'Ride Accepted'),
        ('RIDE_STARTED', 'Ride Started'),
        ('RIDE_COMPLETED', 'Ride Completed'),
        ('RIDE_CANCELLED', 'Ride Cancelled'),
        ('PAYMENT', 'Payment'),
        ('SYSTEM', 'System'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_to_type = models.CharField(max_length=50, null=True, blank=True)
    related_to_id = models.IntegerField(null=True, blank=True)
    action_url = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
