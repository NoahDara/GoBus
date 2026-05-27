from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment


@receiver(post_save, sender=Payment)
def on_payment_confirmed(sender, instance, **kwargs):
    """
    When a payment is marked as paid, the booking status
    is automatically updated to 'confirmed' (handled in model.mark_paid()).
    
    This signal is a placeholder for future payment-related logic:
    - Send confirmation emails
    - Generate e-ticket
    - Update seat availability
    - Log audit trail
    """
    if instance.status == Payment.STATUS_PAID:
        # TODO: Add post-payment actions here
        # - send_booking_confirmation_email(instance.booking)
        # - generate_ticket(instance.booking)
        pass
  