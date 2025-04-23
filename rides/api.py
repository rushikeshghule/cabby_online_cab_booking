from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from .models import Ride
from accounts.models import Notification

def ride_status(request, ride_id):
    """
    API endpoint to get the current status of a ride.
    This endpoint is used by the fallback polling mechanism when WebSockets are not available.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Get the ride
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Debug info
    print(f"Ride status request: Ride #{ride_id}, User: {request.user.username}, Is rider: {ride.rider == request.user}, Is driver: {ride.driver == request.user if ride.driver else False}")
    
    # Fixed authorization check - use driver_profile instead of driverprofile
    if ride.rider != request.user and ride.driver != request.user:
        return JsonResponse({'error': 'Not authorized to view this ride'}, status=403)
    
    # Get any unread notifications related to this ride
    unread_notifications = Notification.objects.filter(
        user=request.user,
        related_to_type='Ride',
        related_to_id=ride.id,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Create response with ride status and any relevant messages
    response = {
        'status': ride.status,
        'last_updated': ride.updated_at.isoformat() if ride.updated_at else None,
    }
    
    # Add notification message if available
    if unread_notifications.exists():
        notification = unread_notifications.first()
        response['message'] = notification.message
        
        # Mark notification as read
        notification.is_read = True
        notification.save()
    
    # Add helpful status message if no notifications
    if 'message' not in response:
        status_messages = {
            'REQUESTED': 'Looking for a driver',
            'ACCEPTED': 'A driver has accepted your ride',
            'ARRIVED': 'Driver has arrived at pickup location',
            'STARTED': 'Your ride is in progress',
            'COMPLETED': 'Your ride has been completed',
            'CANCELLED': 'Your ride has been cancelled'
        }
        response['message'] = status_messages.get(ride.status, '')
    
    # If ride is completed or cancelled, add redirect URL
    if ride.status in ['COMPLETED', 'CANCELLED']:
        if request.user == ride.rider:
            response['redirect_url'] = f'/accounts/rider/dashboard/'
        elif request.user == ride.driver:
            response['redirect_url'] = f'/accounts/driver/dashboard/'
    
    return JsonResponse(response)
