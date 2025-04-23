from django.db import models
from django.conf import settings
from rides.models import Ride

class Message(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.get_full_name()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
