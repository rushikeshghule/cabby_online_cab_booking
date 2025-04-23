from django.urls import path
from . import api

urlpatterns = [
    path('notifications/', api.get_notifications, name='api_notifications'),
] 