from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Notification
from rides.models import Ride
from django.urls import reverse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get user's notifications, optionally filtered by timestamp
    """
    # Check if we have a 'since' parameter to filter by timestamp
    since_str = request.GET.get('since', None)
    since_time = None
    
    if since_str:
        try:
            since_time = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            # If parsing fails, ignore the parameter
            pass
    
    # Build notification query
    notification_query = Notification.objects.filter(user=request.user)
    
    # Apply time filter if provided
    if since_time:
        notification_query = notification_query.filter(created_at__gt=since_time)
    else:
        # Without time filter, just get unread notifications
        notification_query = notification_query.filter(is_read=False)
    
    # Get latest notifications
    notifications = notification_query.order_by('-created_at')[:10]
    
    notification_data = [{
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'created_at': notification.created_at.isoformat(),
        'is_read': notification.is_read,
        'action_url': notification.action_url
    } for notification in notifications]
    
    # Check if the user has any active ride for ride status updates
    ride_updates = []
    
    if request.user.is_rider():
        # Get active ride for rider
        active_rides = Ride.objects.filter(
            rider=request.user,
            status__in=['REQUESTED', 'ACCEPTED', 'STARTED']
        ).order_by('-created_at')
    else:
        # Get active ride for driver
        active_rides = Ride.objects.filter(
            driver=request.user,
            status__in=['ACCEPTED', 'STARTED']
        ).order_by('-created_at')
    
    # Format ride updates
    for ride in active_rides:
        status_messages = {
            'REQUESTED': 'Waiting for driver',
            'ACCEPTED': 'Driver is on the way',
            'STARTED': 'Ride in progress',
            'COMPLETED': 'Ride completed',
            'CANCELLED': 'Ride cancelled'
        }
        
        ride_updates.append({
            'id': ride.id,
            'status': ride.status,
            'is_active': True,
            'status_message': status_messages.get(ride.status, ride.status),
            'detail_url': reverse('ride_detail', args=[ride.id])
        })
    
    # Return both notifications and ride updates
    return Response({
        'notifications': notification_data,
        'ride_updates': ride_updates,
        'timestamp': timezone.now().isoformat()
    })