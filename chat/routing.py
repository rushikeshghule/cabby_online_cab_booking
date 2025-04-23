from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Fix the WebSocket URL pattern - no leading 'ws/' since it's added by the protocol router
    re_path(r'chat/(?P<ride_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]