from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from helpers.models import BaseModel
from bookings.models import Booking


class Payment(BaseModel):
    """
    Tracks payment for a booking.
    
    Mobile payment via Paynow (Ecocash USSD).
    Status flow: pending → paid (after Paynow confirms)
    or pending → failed/cancelled
    
    When payment is confirmed, linked Booking status is updated to 'confirmed'.
    """
    
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Booking link
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount in USD (from booking fare)"
    )
    phone_number = models.CharField(
        max_length=20,
        help_text="Ecocash phone number (0XXXXXXXXX)"
    )
    
    # Paynow integration
    payment_reference = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    poll_url = models.URLField(
        db_index=True,
        help_text="Paynow poll URL for status checking"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    paynow_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Status from Paynow (e.g., 'Paid', 'Pending')"
    )
    
    # Confirmation tracking
    confirmed_at = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    # Metadata (for audit/debugging)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data e.g. schedule_id, route_name"
    )
    
    # Status check count
    status_check_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.payment_reference} - {self.amount} USD - {self.status.upper()}"

    def mark_paid(self, paynow_status=None):
        """Mark payment as paid and update booking status"""
        self.status = self.STATUS_PAID
        self.confirmed_at = timezone.now()
        if paynow_status:
            self.paynow_status = paynow_status
        self.save(update_fields=['status', 'confirmed_at', 'paynow_status'])
        
        # Update linked booking to confirmed
        self.booking.status = Booking.STATUS_CONFIRMED
        self.booking.save(update_fields=['status'])

    def mark_failed(self, error_message=None):
        """Mark payment as failed"""
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
        
        # Cancel the booking
        self.booking.status = Booking.STATUS_CANCELLED
        self.booking.save(update_fields=['status'])

    def mark_cancelled(self):
        """Mark payment as cancelled"""
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status'])
        
        # Cancel the booking
        self.booking.status = Booking.STATUS_CANCELLED
        self.booking.save(update_fields=['status'])

    def record_status_check(self, paynow_status=None, paid=False):
        """Record a status check from Paynow polling"""
        self.status_check_count += 1
        self.last_checked = timezone.now()
        
        if paynow_status:
            self.paynow_status = paynow_status
        
        if paid and not (self.status == self.STATUS_PAID):
            self.mark_paid(paynow_status)
        else:
            self.save(update_fields=['status_check_count', 'last_checked', 'paynow_status'])

    @classmethod
    def create_from_paynow_response(cls, booking, user, response, phone_number, metadata=None):
        """
        Create a Payment record from Paynow mobile payment response.
        
        Args:
            booking: Booking instance
            user: User instance
            response: Dict from service.create_mobile_payment()
            phone_number: Ecocash phone number
            metadata: Optional dict with additional data
        
        Returns:
            Payment instance (saved to DB)
        """
        if not response.get('success'):
            raise ValueError("Cannot create from failed response")
        
        return cls.objects.create(
            booking=booking,
            user=user,
            amount=booking.fare,
            phone_number=phone_number,
            payment_reference=response['reference'],
            poll_url=response['poll_url'],
            status=cls.STATUS_PENDING,
            metadata=metadata or {}
        )