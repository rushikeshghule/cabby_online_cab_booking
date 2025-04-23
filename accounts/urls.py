from django.urls import path
from . import views
from .api import get_notifications

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/revenue-data/', views.admin_revenue_data, name='admin_revenue_data'),
    path('admin/map-data/', views.admin_map_data, name='admin_map_data'),
    path('admin/approve-driver/<int:user_id>/', views.approve_driver, name='approve_driver'),
    path('admin/reject-driver/<int:user_id>/', views.reject_driver, name='reject_driver'),
    # API endpoints
    path('api/notifications/', get_notifications, name='api_notifications'),
] 