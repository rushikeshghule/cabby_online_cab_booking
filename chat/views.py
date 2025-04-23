from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from rides.models import Ride
from .models import Message
from django.utils import timezone
import json

# Create your views here.

@login_required
def chat_room(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is part of this ride
    if request.user not in [ride.rider, ride.driver]:
        return JsonResponse({'error': 'You do not have permission to access this chat.'}, status=403)
    
    # Get or create chat room
    messages = Message.objects.filter(ride=ride).order_by('created_at')
    
    # Mark messages as read
    unread_messages = messages.filter(
        ~Q(sender=request.user),
        is_read=False
    )
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    context = {
        'ride': ride,
        'messages': messages,
        'other_user': ride.driver if request.user == ride.rider else ride.rider
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def get_messages(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is part of this ride
    if request.user not in [ride.rider, ride.driver]:
        return JsonResponse({'error': 'You do not have permission to access these messages.'}, status=403)
    
    # Get messages after the last_id
    last_id = request.GET.get('last_id')
    messages = Message.objects.filter(ride=ride)
    
    if last_id:
        messages = messages.filter(id__gt=last_id)
    
    # Mark messages as read
    unread_messages = messages.filter(
        ~Q(sender=request.user),
        is_read=False
    )
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    messages_data = [{
        'id': msg.id,
        'sender_id': msg.sender.id,
        'content': msg.content,
        'created_at': msg.created_at.strftime('%H:%M'),
        'is_read': msg.is_read
    } for msg in messages]
    
    return JsonResponse(messages_data, safe=False)

@login_required
def send_message(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is part of this ride
    if request.user not in [ride.rider, ride.driver]:
        return JsonResponse({'error': 'You do not have permission to access this chat.'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            receiver_id = data.get('receiver_id')
            
            if not content:
                return JsonResponse({'error': 'Message content is required.'}, status=400)
                
            # Create message
            message = Message.objects.create(
                ride=ride,
                sender=request.user,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'created_at': message.created_at.strftime('%H:%M')
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def mark_messages_read(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is part of this ride
    if request.user not in [ride.rider, ride.driver]:
        return JsonResponse({'error': 'You do not have permission to access this chat.'}, status=403)
    
    if request.method == 'POST':
        # Mark all messages from the other user as read
        if request.user == ride.rider:
            other_user = ride.driver
        else:
            other_user = ride.rider
        
        if other_user:
            Message.objects.filter(
                ride=ride,
                sender=other_user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)
