from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from bookings.models import Booking
from payments.models import Payment
from .models import Notification
from .helpers import send_booking_confirmation, send_payment_confirmation


@receiver(post_save, sender=Booking)
def on_booking_created(sender, instance, created, **kwargs):
    """
    When a booking is created, send a confirmation notification.
    """
    if created:
        send_booking_confirmation(instance)


@receiver(post_save, sender=Payment)
def on_payment_confirmed(sender, instance, **kwargs):
    """
    When a payment is marked as paid, send a confirmation notification.
    """
    if instance.status == Payment.STATUS_PAID:
        send_payment_confirmation(instance)