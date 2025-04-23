from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('<int:ride_id>/', views.chat_room, name='chat_room'),
    path('<int:ride_id>/messages/', views.get_messages, name='get_messages'),
    path('send-message/<int:ride_id>/', views.send_message, name='send_message'),
    path('mark-read/<int:ride_id>/', views.mark_messages_read, name='mark_messages_read'),
]