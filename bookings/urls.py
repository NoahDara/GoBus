# bookings/urls.py - SIMPLIFIED VERSION

from django.urls import path
from . import views

urlpatterns = [
    # Only need create endpoint
    # Dashboard shows bookings, payment shows payment
    # Everything else on dashboard
    
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),
]