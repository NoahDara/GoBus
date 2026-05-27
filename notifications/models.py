from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from helpers.models import BaseModel
from bookings.models import Booking
from payments.models import Payment


class Notification(BaseModel):
    """
    Audit trail for all notifications sent to users.
    
    Records booking confirmations, payment confirmations, cancellations, etc.
    Supports both email and SMS channels.
    """
    
    CHANNEL_EMAIL = 'email'
    CHANNEL_SMS = 'sms'
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_SMS, 'SMS'),
    ]
    
    TYPE_BOOKING_CONFIRMATION = 'booking_confirmation'
    TYPE_PAYMENT_CONFIRMED = 'payment_confirmed'
    TYPE_BOOKING_CANCELLED = 'booking_cancelled'
    TYPE_PAYMENT_FAILED = 'payment_failed'
    
    TYPE_CHOICES = [
        (TYPE_BOOKING_CONFIRMATION, 'Booking Confirmation'),
        (TYPE_PAYMENT_CONFIRMED, 'Payment Confirmed'),
        (TYPE_BOOKING_CANCELLED, 'Booking Cancelled'),
        (TYPE_PAYMENT_FAILED, 'Payment Failed'),
    ]
    
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # User reference
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Business logic references
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    
    # Notification details
    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES
    )
    recipient = models.CharField(
        max_length=255,
        help_text="Email address or phone number"
    )
    
    # Content
    subject = models.CharField(
        max_length=255,
        blank=True,
        help_text="Email subject (not used for SMS)"
    )
    message = models.TextField()
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} → {self.recipient} ({self.status})"
    
    class Meta:
        ordering = ['-created']
    
    def mark_sent(self):
        """Mark notification as sent"""
        self.status = self.STATUS_SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_failed(self, error_message=None):
        """Mark notification as failed"""
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])