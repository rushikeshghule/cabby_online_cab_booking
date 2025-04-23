from django.conf import settings
from .models import Notification

def notifications(request):
    """
    Add unread notifications count to the template context
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {
            'unread_notifications_count': unread_count
        }
    return {
        'unread_notifications_count': 0
    }

def user_status(request):
    """
    Add user availability status to the template context for drivers
    """
    context = {
        'is_available': False
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'driver_profile'):
        context['is_available'] = request.user.driver_profile.is_available
    
    return context 