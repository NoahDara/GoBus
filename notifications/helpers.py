from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking):
    """
    Send booking confirmation email to user.
    Creates a Notification record for audit trail.
    
    Args:
        booking: Booking instance
    """
    try:
        user = booking.user
        recipient = user.email
        
        # Prepare email content
        subject = f"Booking Confirmation - {booking.booking_reference}"
        
        context = {
            'user': user,
            'booking': booking,
            'schedule': booking.schedule,
            'route': booking.schedule.route,
            'boarding_stop': booking.boarding_stop,
            'alighting_stop': booking.alighting_stop,
            'fare': booking.fare,
            'reference': booking.booking_reference,
        }
        
        # Render email template
        message = render_to_string('emails/booking_confirmation.html', context)
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            booking=booking,
            notification_type=Notification.TYPE_BOOKING_CONFIRMATION,
            channel=Notification.CHANNEL_EMAIL,
            recipient=recipient,
            subject=subject,
            message=message,
            status=Notification.STATUS_PENDING
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=message,
            fail_silently=False
        )
        
        notification.mark_sent()
        logger.info(f"✅ Booking confirmation sent: {booking.booking_reference} → {recipient}")
    
    except Exception as e:
        logger.error(f"❌ Error sending booking confirmation: {str(e)}", exc_info=True)
        if 'notification' in locals():
            notification.mark_failed(str(e))


def send_payment_confirmation(payment):
    """
    Send payment confirmation email to user.
    Creates a Notification record for audit trail.
    
    Args:
        payment: Payment instance
    """
    try:
        user = payment.user
        booking = payment.booking
        recipient = user.email
        
        # Prepare email content
        subject = f"Payment Confirmed - {payment.payment_reference}"
        
        context = {
            'user': user,
            'payment': payment,
            'booking': booking,
            'amount': payment.amount,
            'reference': payment.payment_reference,
        }
        
        # Render email template
        message = render_to_string('emails/payment_confirmation.html', context)
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            payment=payment,
            booking=booking,
            notification_type=Notification.TYPE_PAYMENT_CONFIRMED,
            channel=Notification.CHANNEL_EMAIL,
            recipient=recipient,
            subject=subject,
            message=message,
            status=Notification.STATUS_PENDING
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=message,
            fail_silently=False
        )
        
        notification.mark_sent()
        logger.info(f"✅ Payment confirmation sent: {payment.payment_reference} → {recipient}")
    
    except Exception as e:
        logger.error(f"❌ Error sending payment confirmation: {str(e)}", exc_info=True)
        if 'notification' in locals():
            notification.mark_failed(str(e))


def send_booking_cancellation(booking, reason=None):
    """
    Send booking cancellation notification to user.
    Called manually when a booking is cancelled.
    
    Args:
        booking: Booking instance
        reason: Optional cancellation reason
    """
    try:
        user = booking.user
        recipient = user.email
        
        subject = f"Booking Cancelled - {booking.booking_reference}"
        
        context = {
            'user': user,
            'booking': booking,
            'reason': reason or 'Your booking has been cancelled.',
        }
        
        message = render_to_string('emails/booking_cancellation.html', context)
        
        notification = Notification.objects.create(
            user=user,
            booking=booking,
            notification_type=Notification.TYPE_BOOKING_CANCELLED,
            channel=Notification.CHANNEL_EMAIL,
            recipient=recipient,
            subject=subject,
            message=message,
            status=Notification.STATUS_PENDING
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=message,
            fail_silently=False
        )
        
        notification.mark_sent()
        logger.info(f"✅ Cancellation notification sent: {booking.booking_reference} → {recipient}")
    
    except Exception as e:
        logger.error(f"❌ Error sending cancellation notification: {str(e)}", exc_info=True)
        if 'notification' in locals():
            notification.mark_failed(str(e))


def send_payment_failed(payment, error_message=None):
    """
    Send payment failure notification to user.
    Called when payment fails.
    
    Args:
        payment: Payment instance
        error_message: Error message to include
    """
    try:
        user = payment.user
        booking = payment.booking
        recipient = user.email
        
        subject = f"Payment Failed - {payment.payment_reference}"
        
        context = {
            'user': user,
            'payment': payment,
            'booking': booking,
            'error': error_message or 'Your payment could not be processed.',
        }
        
        message = render_to_string('emails/payment_failed.html', context)
        
        notification = Notification.objects.create(
            user=user,
            payment=payment,
            booking=booking,
            notification_type=Notification.TYPE_PAYMENT_FAILED,
            channel=Notification.CHANNEL_EMAIL,
            recipient=recipient,
            subject=subject,
            message=message,
            status=Notification.STATUS_PENDING
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=message,
            fail_silently=False
        )
        
        notification.mark_sent()
        logger.info(f"✅ Payment failure notification sent: {payment.payment_reference} → {recipient}")
    
    except Exception as e:
        logger.error(f"❌ Error sending payment failure notification: {str(e)}", exc_info=True)
        if 'notification' in locals():
            notification.mark_failed(str(e))