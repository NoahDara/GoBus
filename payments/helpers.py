from paynow import Paynow
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

from .models import Payment

# ============================================================================
# PAYNOW SERVICE — Mobile Payment Only
# ============================================================================

class PaynowMobileService:
    """
    Handles Ecocash mobile payments via Paynow.
    
    Adapted from ERP system — mobile payment only, no online payment.
    """
    
    def __init__(self):
        """Initialize Paynow with settings"""
        self.integration_id = settings.PAYNOW_INTEGRATION_ID
        self.integration_key = settings.PAYNOW_INTEGRATION_KEY
        
        if not self.integration_id or not self.integration_key:
            raise ValueError(
                "PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY not configured"
            )
        
        self.paynow = Paynow(
            integration_id=self.integration_id,
            integration_key=self.integration_key,
            result_url=self._get_callback_url('paynow-result'),
            return_url=self._get_callback_url('paynow-return')
        )
    
    def _get_callback_url(self, url_name):
        """Get full callback URL for Paynow"""
        relative_url = reverse(url_name)
        domain = getattr(settings, 'PAYNOW_DOMAIN', 'localhost:8000')
        domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
        protocol = 'http' if settings.DEBUG else 'https'
        return f"{protocol}://{domain}{relative_url}"
    
    def create_mobile_payment(self, reference, email, amount, phone_number, description="Booking"):
        """
        Create an Ecocash mobile payment.
        
        Args:
            reference: Unique reference (e.g., 'BOOKING-UUID')
            email: Customer email
            amount: Amount in USD
            phone_number: Ecocash number (0777xxxxxx)
            description: Item description
        
        Returns:
            dict: {
                'success': bool,
                'reference': str,
                'poll_url': str (if success),
                'error': str (if not success)
            }
        """
        try:
            logger.info(f"Creating mobile payment: {reference} for {phone_number}")
            
            # Validate phone
            if not phone_number.startswith('0') or len(phone_number) != 10:
                return {
                    'success': False,
                    'error': 'Invalid phone. Use format: 0777xxxxxx'
                }
            
            # Create payment
            payment = self.paynow.create_payment(reference, email)
            payment.add(description, float(amount))
            
            # Send mobile payment request
            response = self.paynow.send_mobile(payment, phone_number, 'ecocash')
            
            if response.success:
                logger.info(f"✅ Mobile payment created: {reference} - ${amount}")
                return {
                    'success': True,
                    'reference': reference,
                    'amount': amount,
                    'phone_number': phone_number,
                    'poll_url': response.poll_url,
                    'instructions': response.instructions
                }
            else:
                error_msg = getattr(response, 'error', 'Unknown error')
                if isinstance(error_msg, type):
                    error_msg = 'Mobile payment creation failed'
                logger.error(f"❌ Paynow error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            logger.error(f"❌ Error creating mobile payment: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_payment_status(self, poll_url):
        """
        Check payment status.
        
        Returns:
            dict: {
                'success': bool,
                'paid': bool,
                'status': str (e.g., 'Paid')
            }
        """
        try:
            logger.info(f"Checking payment status: {poll_url}")
            status = self.paynow.check_transaction_status(poll_url)
            
            return {
                'success': True,
                'paid': getattr(status, 'paid', False),
                'status': getattr(status, 'status', 'Unknown')
            }
        
        except Exception as e:
            logger.error(f"❌ Error checking status: {str(e)}", exc_info=True)
            return {
                'success': False,
                'paid': False,
                'error': str(e)
            }


def get_paynow_service():
    """Get Paynow service instance (singleton)"""
    global _service
    if '_service' not in globals():
        _service = PaynowMobileService()
    return _service


# ============================================================================
# PAYMENT TRACKER — Create & Track Payments
# ============================================================================

class BookingPaymentTracker:
    """
    Creates and tracks mobile payments for bookings.
    
    Usage:
        tracker = BookingPaymentTracker()
        
        payment = tracker.create_mobile_payment(
            booking=booking,
            user=request.user,
            phone_number='0777832735',
            metadata={'route_id': route.uid}
        )
    """
    
    def __init__(self):
        self.service = get_paynow_service()
    
    def create_mobile_payment(self, booking, user, phone_number, metadata=None):
        """
        Create mobile payment for a booking.
        
        Args:
            booking: Booking instance
            user: User instance
            phone_number: Ecocash number
            metadata: Optional dict
        
        Returns:
            Payment instance (if successful) or None (if failed)
        """
        try:
            # Generate reference from booking
            reference = f"BOOKING-{booking.uid}"
            
            # Create payment via Paynow
            response = self.service.create_mobile_payment(
                reference=reference,
                email=user.email,
                amount=float(booking.fare),
                phone_number=phone_number,
                description=f"Bus booking: {booking.schedule.route.name}"
            )
            
            if not response['success']:
                logger.error(f"Payment creation failed: {response['error']}")
                return None
            
            # Save to database
            payment = Payment.create_from_paynow_response(
                booking=booking,
                user=user,
                response=response,
                phone_number=phone_number,
                metadata=metadata or {}
            )
            
            logger.info(f"Payment recorded: {reference}")
            return payment
        
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            return None
    
    def check_and_update_status(self, payment_id):
        """
        Check payment status and update Payment + Booking records.
        
        Args:
            payment_id: Payment UUID or ID
        
        Returns:
            bool: True if paid, False otherwise
        """
        try:
            payment = Payment.objects.get(uid=payment_id)
            
            # Check status via Paynow
            status = self.service.check_payment_status(payment.poll_url)
            
            if not status['success']:
                logger.error(f"Error checking status: {status.get('error')}")
                return False
            
            # Update audit trail
            payment.record_status_check(
                paynow_status=status.get('status'),
                paid=status.get('paid', False)
            )
            
            return status.get('paid', False)
        
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_id}")
            return False
        except Exception as e:
            logger.error(f"Error checking status: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def get_payment_by_reference(reference):
        """Get payment by reference"""
        try:
            return Payment.objects.get(payment_reference=reference)
        except Payment.DoesNotExist:
            return None