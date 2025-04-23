from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, DriverProfile, RiderProfile, Notification
from rides.models import Ride
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json
from django.core.mail import send_mail
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

def home(request):
    return render(request, 'accounts/home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        if role == 'RIDER':
            RiderProfile.objects.create(user=user)
        elif role == 'DRIVER':
            DriverProfile.objects.create(user=user)
        
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'accounts/register.html')

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.phone_number = request.POST.get('phone_number')
        
        user.save()
        
        if user.is_driver():
            profile = user.driver_profile
            profile.vehicle_number = request.POST.get('vehicle_number')
            profile.vehicle_type = request.POST.get('vehicle_type')
            profile.license_number = request.POST.get('license_number')
            
            if 'license_document' in request.FILES:
                profile.license_document = request.FILES['license_document']
            if 'insurance_document' in request.FILES:
                profile.insurance_document = request.FILES['insurance_document']
                
            profile.save()
        elif user.is_rider():
            profile = user.rider_profile
            profile.home_address = request.POST.get('home_address')
            profile.work_address = request.POST.get('work_address')
            profile.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html')

@login_required
def dashboard(request):
    if request.user.is_driver():
        # Get active ride
        active_ride = Ride.objects.filter(
            driver=request.user,
            status__in=['ACCEPTED', 'STARTED']
        ).first()
        
        # Get recent rides
        recent_rides = Ride.objects.filter(
            driver=request.user
        ).order_by('-created_at')[:10]
        
        # Calculate today's earnings
        today = timezone.now().date()
        todays_earnings = Ride.objects.filter(
            driver=request.user,
            status='COMPLETED',
            completed_at__date=today
        ).aggregate(total=Sum('fare'))['total'] or 0
        
        # Calculate total earnings
        total_earnings = Ride.objects.filter(
            driver=request.user,
            status='COMPLETED'
        ).aggregate(total=Sum('fare'))['total'] or 0
        
        # Get today's completed rides count
        today_completed_rides = Ride.objects.filter(
            driver=request.user,
            status='COMPLETED',
            completed_at__date=today
        ).count()
        
        # Get online hours (placeholder for now)
        online_hours = 0
        
        context = {
            'active_ride': active_ride,
            'recent_rides': recent_rides,
            'todays_earnings': todays_earnings,
            'total_earnings': total_earnings,
            'today_completed_rides': today_completed_rides,
            'online_hours': online_hours
        }
        return render(request, 'accounts/driver_dashboard.html', context)
    elif request.user.is_rider():
        # Get active ride for rider
        active_ride = Ride.objects.filter(
            rider=request.user,
            status__in=['PENDING', 'ACCEPTED', 'STARTED']
        ).first()
        
        # Get recent rides for rider
        recent_rides = Ride.objects.filter(
            rider=request.user
        ).order_by('-created_at')[:10]
        
        context = {
            'active_ride': active_ride,
            'recent_rides': recent_rides
        }
        return render(request, 'accounts/rider_dashboard.html', context)
    else:
        return render(request, 'accounts/admin_dashboard.html')

@staff_member_required
def admin_dashboard(request):
    # Get current date range
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # User stats
    total_users = User.objects.count()
    rider_count = User.objects.filter(is_rider=True).count()
    driver_count = User.objects.filter(is_driver=True).count()
    
    # Ride stats
    active_rides = Ride.objects.filter(status__in=['ACCEPTED', 'STARTED'])
    active_rides_count = active_rides.count()
    completed_rides_today = Ride.objects.filter(
        status='COMPLETED',
        completed_at__date=today
    ).count()
    
    # Revenue stats
    today_revenue = Ride.objects.filter(
        status='COMPLETED',
        completed_at__date=today
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    yesterday_revenue = Ride.objects.filter(
        status='COMPLETED',
        completed_at__date=yesterday
    ).aggregate(total=Sum('fare'))['total'] or 1  # Avoid division by zero
    
    revenue_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
    
    # Pending approvals
    pending_approvals = DriverProfile.objects.filter(is_approved=False)
    
    context = {
        'total_users': total_users,
        'rider_count': rider_count,
        'driver_count': driver_count,
        'active_rides_count': active_rides_count,
        'completed_rides_today': completed_rides_today,
        'today_revenue': today_revenue,
        'revenue_growth': revenue_growth,
        'pending_approvals_count': pending_approvals.count(),
        'active_rides': active_rides.select_related('rider', 'driver'),
        'pending_approvals': pending_approvals.select_related('user')
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)

@staff_member_required
def admin_revenue_data(request):
    period = request.GET.get('period', 'week')
    today = timezone.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
        date_format = '%a'
    elif period == 'month':
        start_date = today - timedelta(days=30)
        date_format = '%d %b'
    else:  # year
        start_date = today - timedelta(days=365)
        date_format = '%b %Y'
    
    revenue_data = Ride.objects.filter(
        status='COMPLETED',
        completed_at__date__gte=start_date,
        completed_at__date__lte=today
    ).values('completed_at__date').annotate(
        total=Sum('fare')
    ).order_by('completed_at__date')
    
    labels = []
    values = []
    
    current_date = start_date
    while current_date <= today:
        daily_revenue = next(
            (item['total'] for item in revenue_data if item['completed_at__date'] == current_date),
            0
        )
        labels.append(current_date.strftime(date_format))
        values.append(float(daily_revenue))
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'labels': labels,
        'values': values
    })

@staff_member_required
def admin_map_data(request):
    # Get active drivers
    active_drivers = DriverProfile.objects.filter(
        is_approved=True,
        is_active=True,
        last_location_update__gte=timezone.now() - timedelta(minutes=5)
    ).select_related('user')
    
    # Get active rides
    active_rides = Ride.objects.filter(
        status__in=['ACCEPTED', 'STARTED']
    )
    
    # Format driver data
    drivers_data = [{
        'id': driver.id,
        'name': driver.user.get_full_name(),
        'lat': driver.current_latitude,
        'lng': driver.current_longitude
    } for driver in active_drivers]
    
    # Format ride data
    rides_data = [{
        'id': ride.id,
        'pickup_lat': ride.pickup_latitude,
        'pickup_lng': ride.pickup_longitude,
        'dropoff_lat': ride.dropoff_latitude,
        'dropoff_lng': ride.dropoff_longitude
    } for ride in active_rides]
    
    return JsonResponse({
        'drivers': drivers_data,
        'rides': rides_data
    })

@staff_member_required
def approve_driver(request, user_id):
    if request.method == 'POST':
        driver = get_object_or_404(DriverProfile, user_id=user_id)
        driver.is_approved = True
        driver.approved_at = timezone.now()
        driver.save()
        
        # Send approval notification
        Notification.objects.create(
            user=driver.user,
            title='Driver Application Approved',
            message='Your driver application has been approved. You can now start accepting rides.'
        )
    
    return redirect('admin_dashboard')

@staff_member_required
def reject_driver(request, user_id):
    if request.method == 'POST':
        driver = get_object_or_404(DriverProfile, user_id=user_id)
        driver.delete()
        
        # Send rejection notification
        Notification.objects.create(
            user=driver.user,
            title='Driver Application Rejected',
            message='Your driver application has been rejected. Please contact support for more information.'
        )
    
    return redirect('admin_dashboard')

@login_required
def notifications(request):
    notifications = request.user.notifications.all()
    unread_notifications = notifications.filter(is_read=False)
    
    # Mark all as read
    if request.method == 'POST':
        unread_notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    
    context = {
        'notifications': notifications,
        'unread_count': unread_notifications.count()
    }
    return render(request, 'accounts/notifications.html', context)

@login_required
def toggle_availability(request):
    if not request.user.is_driver:
        messages.error(request, 'Only drivers can toggle availability.')
        return redirect('dashboard')
        
    driver_profile = request.user.driver_profile
    driver_profile.is_available = not driver_profile.is_available
    driver_profile.save()
    
    messages.success(request, 
        'You are now {}line'.format('on' if driver_profile.is_available else 'off'))
    return redirect('dashboard')
