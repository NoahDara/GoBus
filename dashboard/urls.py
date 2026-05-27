# dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard (routes based on user role)
    path('', views.DashboardBaseView.as_view(), name='dashboard'),
    
    # Role-specific dashboards
    path('admin/', views.AdminDashboardView.as_view(), name='dashboard-admin'),
    path('driver/', views.DriverDashboardView.as_view(), name='dashboard-driver'),
    path('passenger/', views.PassengerDashboardView.as_view(), name='dashboard-passenger'),
]