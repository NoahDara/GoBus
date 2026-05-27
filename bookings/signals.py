from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from .helpers import generate_booking_reference


@receiver(post_save, sender=Booking)
def on_booking_created(sender, instance, created, **kwargs):
    """
    Generates a unique booking reference when a booking is first created.
    """
    if created and not instance.booking_reference:
        ref = generate_booking_reference(instance)
        Booking.objects.filter(uid=instance.uid).update(booking_reference=ref)