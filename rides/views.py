from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import AnonymousUser
from collections import defaultdict
import calendar
from datetime import timedelta
import json
from decimal import Decimal, InvalidOperation
from .models import Ride
from accounts.models import User, DriverProfile
from django.conf import settings
from accounts.utils import send_notification, send_ride_status_update

@login_required
def book_ride(request):
    if request.method == 'POST':
        print("DEBUG book_ride - POST dict:", request.POST.dict())
        try:
            # Extract form data
            pickup_location = request.POST.get('pickup_location')
            dropoff_location = request.POST.get('dropoff_location')
            pickup_latitude = request.POST.get('pickup_latitude')
            pickup_longitude = request.POST.get('pickup_longitude')
            dropoff_latitude = request.POST.get('dropoff_latitude')
            dropoff_longitude = request.POST.get('dropoff_longitude')
            fare = request.POST.get('fare')
            
            # Validate required fields
            required_fields = [
                'pickup_location', 'dropoff_location',
                'pickup_latitude', 'pickup_longitude',
                'dropoff_latitude', 'dropoff_longitude',
                'fare'
            ]
            missing_fields = [f for f in required_fields if not request.POST.get(f)]
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
            
            # Create the ride
            ride = Ride.objects.create(
                rider=request.user,
                pickup_address=pickup_location,
                dropoff_address=dropoff_location,
                pickup_latitude=float(pickup_latitude),
                pickup_longitude=float(pickup_longitude),
                dropoff_latitude=float(dropoff_latitude),
                dropoff_longitude=float(dropoff_longitude),
                fare=Decimal(str(fare)),
                status='REQUESTED'
            )

            # Store additional info in session for later use
            request.session['vehicle_type'] = request.POST.get('vehicle_type')
            request.session['payment_method'] = request.POST.get('payment_method')
            request.session['ride_notes'] = request.POST.get('notes')

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('ride_detail', args=[ride.id])
            })
            
        except (ValueError, TypeError, InvalidOperation) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid data format: {str(e)}'
            }, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON data: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            
    return render(request, 'rides/book_ride.html')

@login_required
def ride_history(request):
    # Get filter parameters
    status = request.GET.get('status', '')
    date_range = request.GET.get('date_range', 'all')
    sort_by = request.GET.get('sort_by', 'date')
    
    # Base queryset - fix for rider view
    if hasattr(request.user, 'driver_profile') and request.user.driver_profile is not None:
        rides = Ride.objects.filter(driver=request.user)
    else:
        rides = Ride.objects.filter(rider=request.user)
    
    # Apply status filter
    if status:
        rides = rides.filter(status=status)
    
    # Apply date filter
    today = timezone.now().date()
    if date_range == 'today':
        rides = rides.filter(created_at__date=today)
    elif date_range == 'week':
        start_of_week = today - timezone.timedelta(days=today.weekday())
        rides = rides.filter(created_at__date__gte=start_of_week)
    elif date_range == 'month':
        rides = rides.filter(created_at__month=today.month, created_at__year=today.year)
    elif date_range == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            rides = rides.filter(created_at__date__gte=start_date)
        if end_date:
            rides = rides.filter(created_at__date__lte=end_date)
    
    # Apply sorting
    if sort_by == 'fare':
        rides = rides.order_by('-fare')
    elif sort_by == 'distance':
        rides = rides.order_by('-distance')
    else:  # Default to date
        rides = rides.order_by('-created_at')
    
    # Debug log
    print(f"User: {request.user}, Is driver: {hasattr(request.user, 'driver_profile')}, Rides found: {rides.count()}")
    
    # Get status choices for the filter dropdown
    status_choices = Ride.STATUS_CHOICES
    
    context = {
        'rides': rides,
        'status_choices': status_choices,
        'selected_status': status,
        'date_range': date_range,
        'sort_by': sort_by,
        'is_driver': hasattr(request.user, 'driver_profile') and request.user.driver_profile is not None
    }
    
    return render(request, 'rides/ride_history.html', context)

@login_required
def ride_detail(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    if request.user != ride.rider and request.user != ride.driver:
        messages.error(request, 'You do not have permission to view this ride.')
        return redirect('dashboard')
    return render(request, 'rides/ride_detail.html', {'ride': ride})

@login_required
def accept_ride(request, ride_id):
    if not request.user.is_driver:
        messages.error(request, 'Only drivers can accept rides.')
        return redirect('dashboard')
        
    ride = get_object_or_404(Ride, id=ride_id)
    if ride.status != 'REQUESTED':
        messages.error(request, 'This ride is no longer available.')
        return redirect('dashboard')
        
    ride.driver = request.user
    ride.status = 'ACCEPTED'
    ride.save()
    
    messages.success(request, 'Ride accepted successfully.')
    return redirect('ride_detail', ride_id=ride_id)

@login_required
def start_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is the driver of this ride
    if request.user != ride.driver:
        messages.error(request, "You are not authorized to start this ride.")
        return redirect('dashboard')
    
    # Check if the ride status is valid for starting
    if ride.status != 'ACCEPTED':
        messages.error(request, "This ride cannot be started.")
        return redirect('ride_detail', ride_id=ride_id)
    
    # Update ride status
    ride.status = 'STARTED'
    ride.started_at = timezone.now()
    ride.save()
    
    # Send real-time notification to rider
    notification_msg = "Your ride has started"
    send_ride_status_update(
        user=ride.rider,
        ride=ride,
        status='STARTED',
        message=notification_msg,
        redirect_url=reverse('ride_detail', args=[ride_id])
    )
    
    messages.success(request, "Ride started successfully!")
    return redirect('ride_detail', ride_id=ride_id)

@login_required
def complete_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is the driver of this ride
    if request.user != ride.driver:
        messages.error(request, "You are not authorized to complete this ride.")
        return redirect('dashboard')
    
    # Check if the ride status is valid for completion
    if ride.status != 'STARTED':
        messages.error(request, "This ride cannot be completed.")
        return redirect('ride_detail', ride_id=ride_id)
    
    # Update ride status
    ride.status = 'COMPLETED'
    ride.completed_at = timezone.now()
    ride.save()
    
    # Send real-time notification to rider
    notification_msg = f"Your ride has been completed. Fare: ₹{ride.fare}"
    send_ride_status_update(
        user=ride.rider,
        ride=ride,
        status='COMPLETED',
        message=notification_msg,
        redirect_url=reverse('ride_detail', args=[ride_id])
    )
    
    # Also send a notification to the driver
    driver_msg = f"You've completed the ride and earned ₹{ride.fare}"
    send_notification(
        user=ride.driver,
        title="Ride Completed",
        message=driver_msg,
        related_to=ride,
        action_url=reverse('ride_detail', args=[ride_id])
    )
    
    messages.success(request, "Ride completed successfully!")
    return redirect('ride_detail', ride_id=ride_id)

@login_required
def cancel_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is either the rider or the driver of this ride
    if request.user != ride.rider and request.user != ride.driver:
        messages.error(request, "You are not authorized to cancel this ride.")
        return redirect('dashboard')
    
    # Check if the ride status allows cancellation
    if ride.status not in ['REQUESTED', 'ACCEPTED']:
        messages.error(request, "This ride cannot be cancelled.")
        return redirect('ride_detail', ride_id=ride_id)
    
    # Update ride status
    ride.status = 'CANCELLED'
    ride.cancelled_at = timezone.now()
    ride.save()
    
    # Determine who cancelled and notify the other party
    if request.user == ride.rider:
        cancel_msg = "Ride cancelled by rider"
        if ride.driver:
            send_ride_status_update(
                user=ride.driver,
                ride=ride,
                status='CANCELLED',
                message=f"{ride.rider.get_full_name()} has cancelled the ride",
                redirect_url=reverse('dashboard')
            )
    else:  # Driver cancelled
        cancel_msg = "Ride cancelled by driver"
        send_ride_status_update(
            user=ride.rider,
            ride=ride,
            status='CANCELLED',
            message=f"Driver {ride.driver.get_full_name()} has cancelled your ride",
            redirect_url=reverse('dashboard')
        )
    
    messages.success(request, f"{cancel_msg} successfully!")
    return redirect('dashboard')

@login_required
def rate_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    if request.user != ride.rider:
        messages.error(request, 'Only riders can rate rides.')
        return redirect('dashboard')
        
    if ride.status != 'COMPLETED':
        messages.error(request, 'Only completed rides can be rated.')
        return redirect('ride_detail', ride_id=ride_id)
        
    if request.method == 'POST':
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback')
        
        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            messages.error(request, 'Please provide a valid rating between 1 and 5.')
            return redirect('ride_detail', ride_id=ride_id)
            
        ride.rider_rating = int(rating)
        ride.rider_feedback = feedback
        ride.save()
        
        # Update driver's average rating
        driver_rides = Ride.objects.filter(driver=ride.driver, rider_rating__isnull=False)
        if driver_rides.exists():
            avg_rating = sum(r.rider_rating for r in driver_rides) / driver_rides.count()
            ride.driver.driver_profile.rating = round(avg_rating, 1)
            ride.driver.driver_profile.save()
        
        messages.success(request, 'Thank you for rating your ride!')
        return redirect('ride_detail', ride_id=ride_id)
        
    return render(request, 'rides/rate_ride.html', {'ride': ride})

@login_required
def nearby_drivers(request):
    if not request.GET.get('lat') or not request.GET.get('lng'):
        return JsonResponse({'error': 'Location parameters required'}, status=400)
        
    lat = float(request.GET['lat'])
    lng = float(request.GET['lng'])
    
    # Find available drivers within 5km radius
    available_drivers = DriverProfile.objects.filter(
        is_available=True,
        current_latitude__isnull=False,
        current_longitude__isnull=False
    )
    
    nearby_drivers = []
    for driver in available_drivers:
        distance = calculate_distance(lat, lng, driver.current_latitude, driver.current_longitude)
        if distance <= 5:  # 5km radius
            nearby_drivers.append({
                'id': driver.user.id,
                'name': driver.user.get_full_name(),
                'latitude': driver.current_latitude,
                'longitude': driver.current_longitude,
                'distance': round(distance, 1)
            })
    
    return JsonResponse({'drivers': nearby_drivers})

@login_required
def update_location(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if not lat or not lng:
            return JsonResponse({'error': 'Location parameters required'}, status=400)
            
        if request.user.is_driver:
            profile = request.user.driver_profile
            profile.current_latitude = lat
            profile.current_longitude = lng
            profile.location_updated_at = timezone.now()
            profile.save()
            
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def available_rides(request):
    if not request.user.is_driver:
        return JsonResponse({'error': 'Only drivers can view available rides'}, status=403)
        
    profile = request.user.driver_profile
    
    # Debug information for troubleshooting
    debug_info = {
        'is_available': profile.is_available,
        'has_location': bool(profile.current_latitude and profile.current_longitude),
        'current_latitude': float(profile.current_latitude) if profile.current_latitude else None,
        'current_longitude': float(profile.current_longitude) if profile.current_longitude else None
    }
    
    # Only check availability status, not location
    if not profile.is_available:
        return JsonResponse({'rides': [], 'debug_info': debug_info})
    
    # Find requested rides
    available_rides = []
    requested_rides = Ride.objects.filter(status='REQUESTED', driver__isnull=True)
    
    debug_info['total_requested_rides'] = requested_rides.count()
    
    if not profile.current_latitude or not profile.current_longitude:
        # If driver is available but has no location yet, show ALL rides
        # This ensures a driver without location data can still see available rides
        for ride in requested_rides:
            available_rides.append({
                'id': ride.id,
                'pickup_address': ride.pickup_address,
                'dropoff_address': ride.dropoff_address,
                'fare': str(ride.fare),
                'distance': None,  # Distance is unknown without driver location
                'created_at': ride.created_at.isoformat()
            })
            
        debug_info['location_missing'] = True
        debug_info['showing_all_rides'] = True
    else:
        # Normal location-based filtering with increased radius (20km instead of 10km)
        for ride in requested_rides:
            try:
                distance = calculate_distance(
                    float(profile.current_latitude), 
                    float(profile.current_longitude),
                    float(ride.pickup_latitude),
                    float(ride.pickup_longitude)
                )
                # Increased radius from 10km to 20km for better visibility
                if distance <= 20:  
                    available_rides.append({
                        'id': ride.id,
                        'pickup_address': ride.pickup_address,
                        'dropoff_address': ride.dropoff_address,
                        'fare': str(ride.fare),
                        'distance': round(distance, 1),
                        'created_at': ride.created_at.isoformat()
                    })
            except (ValueError, TypeError) as e:
                # Handle any conversion errors and still show the ride
                available_rides.append({
                    'id': ride.id,
                    'pickup_address': ride.pickup_address,
                    'dropoff_address': ride.dropoff_address,
                    'fare': str(ride.fare),
                    'distance': None,
                    'created_at': ride.created_at.isoformat()
                })
                debug_info['distance_calculation_error'] = str(e)
    
    debug_info['rides_in_range'] = len(available_rides)
    return JsonResponse({'rides': available_rides, 'debug_info': debug_info})

@login_required
def accept_ride_ajax(request, ride_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        ride = Ride.objects.get(id=ride_id)
        
        # Check if ride is still available
        if ride.status != 'REQUESTED' or ride.driver:
            return JsonResponse({
                'success': False,
                'error': 'This ride is no longer available'
            })
        
        # Assign the driver and update status
        ride.driver = request.user
        ride.status = 'ACCEPTED'
        ride.save()
        
        # Send real-time notification to rider
        notification_msg = f"Driver {request.user.get_full_name()} has accepted your ride request"
        send_ride_status_update(
            user=ride.rider,
            ride=ride,
            status='ACCEPTED',
            message=notification_msg,
            driver=request.user,
            redirect_url=reverse('ride_detail', args=[ride_id])
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('ride_detail', args=[ride_id])
        })
        
    except Ride.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Ride not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def calculate_distance(lat1, lon1, lat2, lon2):
    from math import sin, cos, sqrt, atan2, radians
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

@login_required
def driver_earnings(request):
    if not request.user.is_driver:
        return JsonResponse({'error': 'Only drivers can view earnings'}, status=403)
        
    period = request.GET.get('period', 'week')
    today = timezone.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # year
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    
    completed_rides = Ride.objects.filter(
        driver=request.user,
        status='COMPLETED',
        completed_at__date__range=[start_date, end_date]
    )
    
    # Group earnings by date
    earnings_by_date = defaultdict(Decimal)
    for ride in completed_rides:
        date_key = ride.completed_at.date().isoformat()
        earnings_by_date[date_key] += ride.fare
    
    # Format data for chart
    earnings_data = []
    current_date = start_date
    while current_date <= end_date:
        date_key = current_date.isoformat()
        earnings_data.append({
            'date': date_key,
            'amount': str(earnings_by_date.get(date_key, Decimal('0')))
        })
        current_date += timedelta(days=1)
    
    total_earnings = sum(earnings_by_date.values())
    total_rides = completed_rides.count()
    
    return JsonResponse({
        'earnings_data': earnings_data,
        'total_earnings': str(total_earnings),
        'total_rides': total_rides,
        'period': period
    })