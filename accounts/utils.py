import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Notification

def send_notification(user, title, message, related_to=None, action_url=None):
    """
    Create a notification in the database and send it via WebSocket
    
    Args:
        user: The user to send the notification to
        title: Notification title
        message: Notification message content
        related_to: Optional model instance related to this notification (e.g., a Ride)
        action_url: Optional URL to redirect to when clicking the notification
    """
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        related_to_type=related_to.__class__.__name__ if related_to else None,
        related_to_id=related_to.id if related_to else None,
        action_url=action_url
    )
    
    # Get channel layer
    channel_layer = get_channel_layer()
    
    # Send notification to user's personal group
    async_to_sync(channel_layer.group_send)(
        f'user_{user.id}_notifications',
        {
            'type': 'notification_message',
            'notification_id': notification.id,
            'title': title,
            'message': message,
            'created_at': notification.created_at.isoformat(),
            'related_to': f"{related_to.__class__.__name__}_{related_to.id}" if related_to else None,
            'action_url': action_url
        }
    )
    
    return notification

def send_ride_status_update(user, ride, status, message, driver=None, redirect_url=None):
    """
    Send a real-time ride status update via WebSocket
    
    Args:
        user: The user to send the update to
        ride: The ride being updated
        status: New ride status
        message: Update message
        driver: Optional driver user (when a driver accepts a ride)
        redirect_url: Optional URL to redirect to
    """
    # Get channel layer
    channel_layer = get_channel_layer()
    
    # Send ride update to user's personal group
    async_to_sync(channel_layer.group_send)(
        f'user_{user.id}_notifications',
        {
            'type': 'ride_status_update',
            'ride_id': ride.id,
            'status': status,
            'driver_id': driver.id if driver else None,
            'driver_name': f"{driver.first_name} {driver.last_name}" if driver else None,
            'message': message,
            'redirect_url': redirect_url
        }
    )
    
    # Also create a notification in DB for this update
    notification = Notification.objects.create(
        user=user,
        title=f"Ride {status.title()}",
        message=message,
        related_to_type='Ride',
        related_to_id=ride.id,
        action_url=redirect_url
    )
    
    return notification
