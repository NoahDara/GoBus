# payments/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
import hmac
import hashlib

from payments.models import Payment
from bookings.models import Booking
from helpers.emails import send_booking_confirmation_email
from helpers.paynow import PaynowService

logger = logging.getLogger(__name__)


class PaymentInitiateView(LoginRequiredMixin, View):
    """
    Handle payment form submission
    - Show form with booking details
    - Submit to Paynow
    - Create Payment record
    """
    
    def get(self, request, booking_uid):
        """Show payment form"""
        try:
            booking = Booking.objects.get(uid=booking_uid, user=request.user)
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
            return redirect('booking-index')
        
        # Check booking status
        if booking.status != Booking.STATUS_PENDING:
            messages.warning(request, 'Booking is not pending payment.')
            return redirect('booking-detail', booking_uid=booking_uid)
        
        # Check if payment already exists
        if hasattr(booking, 'payment'):
            return redirect('payment-detail', payment_uid=booking.payment.uid)
        
        context = {
            'booking': booking,
            'amount': booking.fare,
            'currency': 'USD',
            'reference': booking.booking_reference,
        }
        
        return render(request, 'payments/form.html', context)
    
    def post(self, request, booking_uid):
        """Handle payment submission"""
        try:
            booking = Booking.objects.get(uid=booking_uid, user=request.user)
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
        
        # Get form data
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate phone
        if not phone_number or not phone_number.startswith('0') or len(phone_number) != 10:
            return JsonResponse({
                'success': False,
                'error': 'Invalid phone number. Use format: 0XXXXXXXXX'
            }, status=400)
        
        try:
            with transaction.atomic():
                # Call Paynow API
                paynow = PaynowService()
                response = paynow.create_mobile_payment(
                    amount=float(booking.fare),
                    phone_number=phone_number,
                    reference=booking.booking_reference,
                    description=f"GoBus Booking - {booking.schedule.route.name}"
                )
                
                if not response.get('success'):
                    logger.warning(f"Paynow error: {response.get('error')}")
                    return JsonResponse({
                        'success': False,
                        'error': response.get('error', 'Payment initiation failed')
                    }, status=400)
                
                # Create Payment record
                payment = Payment.objects.create(
                    booking=booking,
                    user=request.user,
                    amount=booking.fare,
                    phone_number=phone_number,
                    payment_reference=response['reference'],
                    poll_url=response['poll_url'],
                    status=Payment.STATUS_PENDING,
                    metadata={
                        'schedule_id': str(booking.schedule.uid),
                        'route_name': booking.schedule.route.name,
                        'bus_number': booking.schedule.bus.bus_number,
                    }
                )
                
                logger.info(f"Payment created: {payment.payment_reference} for booking {booking.booking_reference}")
                
                return JsonResponse({
                    'success': True,
                    'payment_uid': str(payment.uid),
                    'poll_url': payment.poll_url,
                    'reference': payment.payment_reference,
                })
        
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error initiating payment. Please try again.'
            }, status=500)


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """
    Show payment details and status
    """
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'
    slug_field = 'uid'
    slug_url_kwarg = 'payment_uid'
    
    def get_queryset(self):
        # Only show own payments
        return Payment.objects.filter(user=self.request.user)


class PaymentStatusView(LoginRequiredMixin, View):
    """
    AJAX endpoint to check payment status
    Called periodically by frontend
    """
    
    def get(self, request, payment_uid):
        """
        Check payment status with Paynow
        """
        try:
            payment = Payment.objects.get(uid=payment_uid, user=request.user)
        except Payment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Payment not found'}, status=404)
        
        # If already paid, return immediately
        if payment.status == Payment.STATUS_PAID:
            return JsonResponse({
                'success': True,
                'status': 'paid',
                'message': 'Payment confirmed!',
                'redirect_url': f'/bookings/{payment.booking.uid}/'
            })
        
        # If failed, return
        if payment.status == Payment.STATUS_FAILED:
            return JsonResponse({
                'success': True,
                'status': 'failed',
                'message': 'Payment failed. Please retry.',
            })
        
        try:
            # Poll Paynow
            paynow = PaynowService()
            response = paynow.check_payment_status(payment.poll_url)
            
            if not response:
                return JsonResponse({
                    'success': True,
                    'status': 'pending',
                    'message': 'Waiting for payment...',
                })
            
            paynow_status = response.get('status', '').lower()
            
            # Update payment record
            payment.status_check_count += 1
            payment.last_checked = timezone.now()
            payment.paynow_status = paynow_status
            
            if paynow_status == 'paid':
                # Mark as paid
                with transaction.atomic():
                    payment.mark_paid(paynow_status)
                    booking = payment.booking
                    booking.status = Booking.STATUS_CONFIRMED
                    booking.save()
                    
                    # Send confirmation email (with try/except)
                    try:
                        send_booking_confirmation_email(request, booking)
                    except Exception as e:
                        logger.error(f"Email failed: {str(e)}")
                    
                    logger.info(f"Payment confirmed: {payment.payment_reference}")
                
                return JsonResponse({
                    'success': True,
                    'status': 'paid',
                    'message': 'Payment confirmed!',
                    'redirect_url': f'/bookings/{payment.booking.uid}/'
                })
            
            else:
                payment.save(update_fields=['status_check_count', 'last_checked', 'paynow_status'])
                
                return JsonResponse({
                    'success': True,
                    'status': 'pending',
                    'message': 'Waiting for payment...',
                    'check_count': payment.status_check_count,
                })
        
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error checking status',
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentCallbackView(View):
    """
    Paynow webhook callback
    Receives payment confirmation from Paynow
    """
    
    def post(self, request):
        """
        Paynow sends:
        {
            "reference": "BOOKING_REFERENCE",
            "amount": "100",
            "paid": true/false,
            "status": "Paid|Pending|Failed",
            "timestamp": "2026-05-30 10:30:00",
            "hash": "HMAC signature"
        }
        """
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in payment callback")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Verify signature
        if not self._verify_signature(data):
            logger.warning(f"Invalid signature in callback: {data.get('reference')}")
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        try:
            payment_reference = data.get('reference')
            paid = data.get('paid', False)
            status = data.get('status', '').lower()
            
            # Find payment
            try:
                payment = Payment.objects.get(payment_reference=payment_reference)
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found: {payment_reference}")
                return JsonResponse({'error': 'Payment not found'}, status=404)
            
            with transaction.atomic():
                if paid and status == 'paid':
                    # Mark as paid
                    payment.mark_paid(status)
                    booking = payment.booking
                    booking.status = Booking.STATUS_CONFIRMED
                    booking.save()
                    
                    # Send email
                    try:
                        send_booking_confirmation_email(None, booking)
                    except Exception as e:
                        logger.error(f"Email failed in callback: {str(e)}")
                    
                    logger.info(f"Payment confirmed via callback: {payment_reference}")
                
                else:
                    # Payment failed
                    payment.mark_failed(f"Paynow status: {status}")
                    logger.warning(f"Payment failed: {payment_reference} - {status}")
            
            return JsonResponse({'success': True})
        
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            return JsonResponse({'error': 'Processing error'}, status=500)
    
    def _verify_signature(self, data):
        """Verify Paynow callback signature"""
        from django.conf import settings
        
        # Get signature from data
        provided_hash = data.pop('hash', '')
        
        # Recreate signature
        data_string = json.dumps(data, sort_keys=True)
        secret = settings.PAYNOW_SECRET
        expected_hash = hmac.new(
            secret.encode(),
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare
        return hmac.compare_digest(provided_hash, expected_hash)