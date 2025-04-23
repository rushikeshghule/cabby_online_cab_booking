from django.urls import path
from . import views
from . import api

urlpatterns = [
    path('book/', views.book_ride, name='book_ride'),
    path('history/', views.ride_history, name='ride_history'),
    path('<int:ride_id>/', views.ride_detail, name='ride_detail'),
    path('<int:ride_id>/accept/', views.accept_ride, name='accept_ride'),
    path('<int:ride_id>/start/', views.start_ride, name='start_ride'),
    path('<int:ride_id>/complete/', views.complete_ride, name='complete_ride'),
    path('<int:ride_id>/cancel/', views.cancel_ride, name='cancel_ride'),
    path('<int:ride_id>/rate/', views.rate_ride, name='rate_ride'),
    path('<int:ride_id>/status/', api.ride_status, name='ride_status'),
    path('nearby-drivers/', views.nearby_drivers, name='nearby_drivers'),
    path('update-location/', views.update_location, name='update_location'),
    path('available-rides/', views.available_rides, name='available_rides'),
    path('accept-ride/<int:ride_id>/', views.accept_ride_ajax, name='accept_ride_ajax'),
    path('earnings/', views.driver_earnings, name='driver_earnings'),
]