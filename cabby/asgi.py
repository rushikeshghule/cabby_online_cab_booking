"""
ASGI config for cabby project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

# Set Django settings module first, before importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabby.settings')

# Initialize Django before importing other components
django.setup()

# Then import Django and other modules
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Import routing modules after Django settings are configured
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from accounts.routing import websocket_urlpatterns as notification_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                chat_websocket_urlpatterns + notification_websocket_urlpatterns
            )
        )
    ),
})
