import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .models import Message
from rides.models import Ride
from accounts.models import Notification

User = get_user_model()

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.room_group_name = f'chat_{self.ride_id}'
        
        # Accept the connection even for anonymous users
        self.accept()
        
        user = self.scope.get("user", AnonymousUser())
        if user.is_anonymous:
            # Send connection status but don't join group for anonymous users
            self.send(text_data=json.dumps({
                'status': 'Connected to chat room (anonymous)',
                'authenticated': False
            }))
            return
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        # Send connection status message
        self.send(text_data=json.dumps({
            'status': 'Connected to chat room',
            'authenticated': True
        }))
    
    def disconnect(self, close_code):
        # Leave room group if joined
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
    
    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        ride_id = text_data_json.get('ride_id', '')
        receiver_id = text_data_json.get('receiver_id', '')
        
        try:
            # Get the ride
            ride = Ride.objects.get(id=self.ride_id)
            user = self.scope.get('user', AnonymousUser())
            
            # Handle anonymous users or authentication issues
            if user.is_anonymous:
                user_id = text_data_json.get('sender_id')
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        self.send(text_data=json.dumps({
                            'error': 'User not found'
                        }))
                        return
                else:
                    self.send(text_data=json.dumps({
                        'error': 'Authentication required'
                    }))
                    return
            
            # Create message in database
            db_message = Message.objects.create(
                ride=ride,
                sender=user,
                content=message,
                is_read=False
            )
            
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': user.id,
                    'message_id': db_message.id,
                    'created_at': db_message.created_at.isoformat()
                }
            )
        except Ride.DoesNotExist:
            self.send(text_data=json.dumps({
                'error': 'Ride not found'
            }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        message_id = event.get('message_id')
        created_at = event.get('created_at')
        
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'message_id': message_id,
            'created_at': created_at
        }))
