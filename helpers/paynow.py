# helpers/paynow.py

import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class PaynowService:
    """
    Handle Paynow payment API integration
    Supports: Ecocash, OneMoney
    """
    
    def __init__(self):
        """Initialize with API credentials from Django settings"""
        self.api_key = getattr(settings, 'PAYNOW_API_KEY', '')
        self.secret = getattr(settings, 'PAYNOW_SECRET', '')
        self.merchant_id = getattr(settings, 'PAYNOW_MERCHANT_ID', '')
        
        # Paynow API endpoints
        self.base_url = 'https://api.paynow.co.zw/v1'
        self.mobile_endpoint = f'{self.base_url}/mobile'
        self.status_endpoint = f'{self.base_url}/status'
        
        # Timeout for API calls
        self.timeout = 10
    
    def create_mobile_payment(self, amount, phone_number, reference, description):
        """
        Create a mobile payment request with Paynow
        
        Args:
            amount (float): Payment amount in USD
            phone_number (str): Customer phone number (0XXXXXXXXX)
            reference (str): Unique reference (booking reference)
            description (str): Payment description
        
        Returns:
            dict: {
                'success': bool,
                'reference': str,
                'poll_url': str,
                'redirect_url': str (optional),
                'error': str (if failed)
            }
        """
        try:
            # Validate inputs
            if not amount or amount <= 0:
                return {'success': False, 'error': 'Invalid amount'}
            
            if not phone_number or not phone_number.startswith('0') or len(phone_number) != 10:
                return {'success': False, 'error': 'Invalid phone number'}
            
            # Prepare request payload
            payload = {
                'merchantId': self.merchant_id,
                'amount': float(amount),
                'phone': phone_number,
                'reference': str(reference),
                'description': str(description),
                'returnUrl': f'{settings.SITE_URL}/payments/callback/',  # Optional redirect
            }
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            logger.info(f"Creating Paynow payment: {reference} for ${amount}")
            
            # Make API call
            response = requests.post(
                f'{self.mobile_endpoint}/initiate',
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check response status
            if response.status_code not in [200, 201]:
                error_msg = response.json().get('error', 'Payment initiation failed')
                logger.error(f"Paynow error: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # Parse response
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', 'Payment initiation failed')
                logger.error(f"Paynow error: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            # Return success with payment details
            result = {
                'success': True,
                'reference': data.get('reference', reference),
                'poll_url': data.get('pollUrl'),
                'redirect_url': data.get('redirectUrl'),
            }
            
            logger.info(f"✅ Payment initiated: {reference}")
            return result
        
        except requests.exceptions.Timeout:
            logger.error("Paynow API timeout")
            return {'success': False, 'error': 'API timeout. Please try again.'}
        
        except requests.exceptions.ConnectionError:
            logger.error("Paynow API connection error")
            return {'success': False, 'error': 'Connection error. Please try again.'}
        
        except Exception as e:
            logger.error(f"Paynow error: {str(e)}")
            return {'success': False, 'error': 'Payment initiation failed'}
    
    def check_payment_status(self, poll_url):
        """
        Poll Paynow to check payment status
        
        Args:
            poll_url (str): URL provided by Paynow in initiate response
        
        Returns:
            dict or None: {
                'status': 'Paid'|'Pending'|'Failed',
                'amount': str,
                'reference': str,
                'timestamp': str,
            } or None if still pending
        """
        try:
            if not poll_url:
                logger.warning("No poll_url provided")
                return None
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
            }
            
            logger.debug(f"Checking payment status: {poll_url}")
            
            # Make API call
            response = requests.get(
                poll_url,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check response status
            if response.status_code != 200:
                logger.warning(f"Status check failed: {response.status_code}")
                return None
            
            # Parse response
            data = response.json()
            
            # Check if payment is completed
            status = data.get('status', '').lower()
            
            if status in ['paid', 'success']:
                logger.info(f"✅ Payment confirmed: {data.get('reference')}")
                return {
                    'status': 'Paid',
                    'amount': data.get('amount'),
                    'reference': data.get('reference'),
                    'timestamp': data.get('timestamp'),
                }
            
            elif status in ['pending', 'processing']:
                logger.debug("Payment still pending")
                return None
            
            elif status in ['failed', 'cancelled']:
                logger.warning(f"❌ Payment failed: {status}")
                return {
                    'status': 'Failed',
                    'error': data.get('error', status),
                }
            
            # Unknown status - treat as pending
            logger.debug(f"Unknown status: {status}")
            return None
        
        except requests.exceptions.Timeout:
            logger.error("Status check timeout")
            return None
        
        except requests.exceptions.ConnectionError:
            logger.error("Status check connection error")
            return None
        
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return None
    
    def refund_payment(self, reference, amount):
        """
        Refund a payment
        
        Args:
            reference (str): Payment reference
            amount (float): Refund amount
        
        Returns:
            dict: {
                'success': bool,
                'refund_id': str,
                'error': str (if failed)
            }
        """
        try:
            payload = {
                'merchantId': self.merchant_id,
                'reference': str(reference),
                'amount': float(amount),
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            logger.info(f"Processing refund: {reference} for ${amount}")
            
            response = requests.post(
                f'{self.base_url}/refund',
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code not in [200, 201]:
                error_msg = response.json().get('error', 'Refund failed')
                logger.error(f"Refund error: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            data = response.json()
            
            if not data.get('success'):
                return {'success': False, 'error': data.get('error', 'Refund failed')}
            
            logger.info(f"✅ Refund processed: {reference}")
            return {
                'success': True,
                'refund_id': data.get('refundId'),
            }
        
        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_callback_signature(data, signature):
        """
        Verify Paynow webhook signature
        
        Args:
            data (dict): Callback payload
            signature (str): HMAC signature from Paynow
        
        Returns:
            bool: True if signature is valid
        """
        try:
            import hmac
            import hashlib
            
            secret = settings.PAYNOW_SECRET
            
            # Create signature string from data
            message = json.dumps(data, sort_keys=True)
            
            # Generate expected signature
            expected = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare (constant time)
            return hmac.compare_digest(signature, expected)
        
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False