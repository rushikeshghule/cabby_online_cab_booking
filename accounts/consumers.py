import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from accounts.models import Notification
from rides.models import Ride
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications.
    Uses a group name based on the user's ID to deliver personalized notifications.
    """
    
    async def connect(self):
        """
        Handles the connection logic for the WebSocket consumer.
        Joins the user to a personal notification group.
        """
        # Get user from scope (set by AuthMiddlewareStack)
        self.user = self.scope.get('user', None)
        
        # Anonymous users can still connect but won't get authenticated notifications
        if self.user and self.user.is_authenticated:
            self.user_group_name = f'user_{self.user.id}_notifications'
            
            # Join user group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Accept the connection
            await self.accept()
            
            # Send a connection status message
            await self.send(text_data=json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'Successfully connected to notification channel'
            }))
            
            print(f"User {self.user.id} connected to notification channel")
            
            # Send any unread notifications on connect
            unread_notifications = await self.get_unread_notifications()
            
            if unread_notifications.exists():
                await self.send(text_data=json.dumps({
                    'type': 'unread_notifications',
                    'notifications': [
                        {
                            'id': notification.id,
                            'title': notification.title,
                            'message': notification.message,
                            'created_at': notification.created_at.isoformat(),
                            'is_read': notification.is_read
                        }
                        for notification in unread_notifications
                    ]
                }))
        else:
            # Accept connection for anonymous users too, but with a warning
            await self.accept()
            
            # Send authentication warning
            await self.send(text_data=json.dumps({
                'type': 'connection_status',
                'status': 'warning',
                'message': 'Connected without authentication. Some notifications may not be received.'
            }))
            
            print("Anonymous user connected to notification channel")

    async def disconnect(self, close_code):
        """
        Handles user disconnection by removing them from their notification group.
        """
        # Leave user group if authenticated
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
            print(f"User disconnected from notification channel, code: {close_code}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Currently used for heartbeat and initial setup.
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')
        
        # Handle heartbeat to keep connection alive
        if message_type == 'heartbeat':
            await self.send(text_data=json.dumps({
                'type': 'heartbeat_response',
                'status': 'alive'
            }))
        
        # Handle mark read notification
        elif message_type == 'mark_read':
            notification_id = text_data_json.get('notification_id')
            await self.mark_notification_read(notification_id)
        
        # Handle ping-pong to keep connection alive
        elif message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': text_data_json.get('timestamp')
            }))

    # Receive message from room group
    async def notification_message(self, event):
        """
        Receive notification from group and forward to WebSocket.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    async def ride_status_update(self, event):
        """
        Receive ride status update from group and forward to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'ride_status_update',
            'ride_id': event['ride_id'],
            'status': event['status'],
            'driver_id': event.get('driver_id'),
            'driver_name': event.get('driver_name'),
            'message': event['message'],
            'redirect_url': event.get('redirect_url')
        }))

    @database_sync_to_async
    def get_unread_notifications(self):
        """
        Get unread notifications for the user.
        """
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).order_by('-created_at')[:5]

    async def mark_notification_read(self, notification_id):
        """
        Mark a notification as read.
        """
        try:
            notification = await self.get_notification(notification_id)
            notification.is_read = True
            await self.save_notification(notification)
            
            # Confirm to the client
            await self.send(text_data=json.dumps({
                'type': 'notification_marked_read',
                'notification_id': notification_id
            }))
        except Notification.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Notification not found'
            }))

    @database_sync_to_async
    def get_notification(self, notification_id):
        """
        Get a notification by ID.
        """
        return Notification.objects.get(id=notification_id, user=self.user)

    @database_sync_to_async
    def save_notification(self, notification):
        """
        Save a notification.
        """
        notification.save()
