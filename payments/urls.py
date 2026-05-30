# payments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Payment routes
    path('<uuid:booking_uid>/initiate/', views.PaymentInitiateView.as_view(), name='payment-initiate'),
    path('<uuid:payment_uid>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('<uuid:payment_uid>/status/', views.PaymentStatusView.as_view(), name='payment-status'),
    
    # Webhook (no auth needed)
    path('callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
]