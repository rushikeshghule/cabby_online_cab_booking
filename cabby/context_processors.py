from django.conf import settings

def websocket_settings(request):
    """
    Add WebSocket settings to the template context.
    This makes the WebSocket port available to all templates.
    """
    return {
        'WEBSOCKET_PORT': getattr(settings, 'WEBSOCKET_PORT', 8001),
    }
