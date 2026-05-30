from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import time
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse


from core.email_service import get_email_service

def send_onboarding_reset_password_mail(request, user):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build base reset URL
    reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    

    reset_url = request.build_absolute_uri(reset_path)
    

    subject = "You have been invited to GoBus Portal!"
    message = render_to_string('mail_list/welcome_user.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    get_email_service().send_email(
        subject=subject,
        html_message=message,
        message=message,
        recipient_list=[user.email],
    )
    
def send_password_reset_mail(request, user):
    """
    Send email to existing users who requested password reset.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build base reset URL
    reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    
    reset_url = request.build_absolute_uri(reset_path)
    
    subject = "Password Reset Request - Go Bus"
    message = render_to_string('mail_list/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    get_email_service().send_email(
        subject=subject,
        html_message=message,
        message=message,
        recipient_list=[user.email],
    )


def send_email_from_global_config(email_subject, email_content, user=None, email=None, html_file_path=None):
    if not html_file_path:
        html_file_path = "mail_list/global_email.html"
    if user:
        recipient_email = user.email
        username = user.username
    elif email:
        recipient_email = email
        username = email
    else:
        settings.LOGGER.error("No user or email provided for sending email.")
        return False
    
    
    email_html_content = render_to_string(
        html_file_path,
        {"username": username, "your_email_content": email_content}
    )
    
    # Use plain text version for the message parameter
    plain_message = strip_tags(email_html_content)
    
    try:
        get_email_service().send_email(
            subject=email_subject,
            message=plain_message,
            html_message=email_html_content,
            recipient_list=[recipient_email],
        )
        return True
    except Exception as e:
        error_message = f"Failed to send email to {recipient_email}: {str(e)}"
        settings.LOGGER.error(error_message)
        return False


def send_html_email(
    subject, html_template, text_content, from_email, to_emails, context={}
):
    """
    Sends an HTML email without attachments.

    Args:
        subject (str): Email subject.
        html_template (str): Path to the HTML template.
        text_content (str): Fallback plain text content.
        from_email (str): Sender's email address.
        to_emails (list): List of recipient email addresses.
        context (dict): Context to render the HTML template.

    Returns:
        int: Number of successfully delivered messages (1 if successful).
    """

    # Render the HTML template with the given context
    html_content = render_to_string(html_template, context)

    # Create the email object with plain text and HTML alternatives
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
    msg.attach_alternative(html_content, "text/html")

    # Send the email
    while True:
        try:
            settings.LOGGER.info(f"Sending email to {to_emails}")
            msg.send(fail_silently=False)
            break
        except Exception as e:
            settings.LOGGER.error(f"Error sending email: {e}")
            time.sleep(5)
    return msg.send()


def send_email_with_attachments(
    subject,
    html_template,
    text_content,
    from_email,
    to_emails,
    attachments=None,
    context={},
):
    # Render the HTML template to a string
    html_content = render_to_string(html_template, context)

    # Create the email message object
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
    msg.attach_alternative(html_content, "text/html")

    # Attach each file
    if attachments:
        for attachment in attachments:
            msg.attach(attachment[0], attachment[1].read(), attachment[2])

    # Send the email

    
    try:
        settings.LOGGER.info(f"Sending email to {to_emails}")
        msg.send(fail_silently=False)
    except Exception as e:
        settings.LOGGER.error(f"Error sending email: {e}")
        email_service = settings.EMAIL_SERVICE
        email_service.send_email(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=to_emails,
            html_message=html_content,
        )
        
        
# helpers/emails.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to user
    
    Args:
        booking: Booking instance
    """
    try:
        user = booking.user
        
        context = {
            'user': user,
            'booking': booking,
            'schedule': booking.schedule,
            'route': booking.schedule.route,
            'bus': booking.schedule.bus,
            'seat': booking.seat,
            'boarding_stop': booking.boarding_stop,
            'alighting_stop': booking.alighting_stop,
            'fare': booking.fare,
            'booking_reference': booking.booking_reference,
            'departure_time': booking.schedule.departure_time,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }
        
        # Render HTML template
        html_message = render_to_string('mail_list/booking_confirmation.html', context)
        plain_message = render_to_string('mail_list/booking_confirmation.txt', context)
        
        # Send email
        send_mail(
            subject=f'Your GoBus Booking Confirmed - {booking.booking_reference}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Booking confirmation sent to {user.email} (Booking: {booking.booking_reference})")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending booking confirmation email: {str(e)}")
        return False


def send_payment_confirmation_email(payment):
    """
    Send payment confirmation and ticket to user
    
    Args:
        payment: Payment instance
    """
    try:
        booking = payment.booking
        user = payment.user
        
        context = {
            'user': user,
            'booking': booking,
            'payment': payment,
            'schedule': booking.schedule,
            'route': booking.schedule.route,
            'bus': booking.schedule.bus,
            'seat': booking.seat,
            'boarding_stop': booking.boarding_stop,
            'alighting_stop': booking.alighting_stop,
            'fare': booking.fare,
            'booking_reference': booking.booking_reference,
            'payment_reference': payment.payment_reference,
            'amount_paid': payment.amount,
            'departure_time': booking.schedule.departure_time,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }
        
        # Render HTML template
        html_message = render_to_string('mail_list/payment_confirmation.html', context)
        plain_message = render_to_string('mail_list/payment_confirmation.txt', context)
        
        # Send email
        send_mail(
            subject=f'Payment Confirmed - GoBus Ticket {booking.booking_reference}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Payment confirmation sent to {user.email} (Payment: {payment.payment_reference})")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending payment confirmation email: {str(e)}")
        return False


def send_booking_cancelled_email(booking, reason=''):
    """
    Send booking cancellation email
    
    Args:
        booking: Booking instance
        reason: Cancellation reason
    """
    try:
        user = booking.user
        
        context = {
            'user': user,
            'booking': booking,
            'schedule': booking.schedule,
            'route': booking.schedule.route,
            'booking_reference': booking.booking_reference,
            'reason': reason or booking.cancellation_reason,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }
        
        # Render HTML template
        html_message = render_to_string('mail_list/booking_cancelled.html', context)
        plain_message = render_to_string('mail_list/booking_cancelled.txt', context)
        
        # Send email
        send_mail(
            subject=f'Booking Cancelled - {booking.booking_reference}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Cancellation email sent to {user.email} (Booking: {booking.booking_reference})")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending cancellation email: {str(e)}")
        return False


def send_refund_processed_email(payment, refund_amount):
    """
    Send refund processed email
    
    Args:
        payment: Payment instance
        refund_amount: Amount refunded
    """
    try:
        user = payment.user
        booking = payment.booking
        
        context = {
            'user': user,
            'booking': booking,
            'payment': payment,
            'refund_amount': refund_amount,
            'booking_reference': booking.booking_reference,
            'payment_reference': payment.payment_reference,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        }
        
        # Render HTML template
        html_message = render_to_string('mail_list/refund_processed.html', context)
        plain_message = render_to_string('mail_list/refund_processed.txt', context)
        
        # Send email
        send_mail(
            subject=f'Refund Processed - ${refund_amount}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Refund email sent to {user.email} (Amount: ${refund_amount})")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending refund email: {str(e)}")
        return False