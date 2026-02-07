import uuid
import json
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .exceptions import ChapaAPIError, PaymentVerificationError

logger = logging.getLogger(__name__)


class ChapaClient:
    """
    Chapa Payment Gateway Client using direct HTTP requests
    Official API Documentation: https://developer.chapa.co/
    """
    
    # API Endpoints
    BASE_URL = "https://api.chapa.co/v1"
    INITIALIZE_URL = f"{BASE_URL}/transaction/initialize"
    VERIFY_URL = f"{BASE_URL}/transaction/verify"
    
    def __init__(self):
        self.secret_key = getattr(settings, 'CHAPA_SECRET_KEY', '')
        if not self.secret_key:
            raise ValueError("CHAPA_SECRET_KEY is not configured in settings")
        
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Configure requests session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Timeout settings
        self.timeout = getattr(settings, 'CHAPA_TIMEOUT', 30)
        
        # Enable debug mode for development
        self.debug = getattr(settings, 'DEBUG', False)
    
    def _make_request(self, method: str, url: str, data: Dict = None) -> Dict:
        """
        Make HTTP request to Chapa API with proper error handling
        """
        try:
            logger.info(f"Making {method} request to {url}")
            
            if self.debug:
                logger.debug(f"Request data: {data}")
            
            if method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    timeout=self.timeout,
                    verify=True  # Always verify SSL
                )
            elif method.upper() == 'GET':
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    verify=True
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log response for debugging
            if self.debug:
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response body: {response.text}")
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                raise ChapaAPIError(
                    f"Bad Request: {error_data.get('message', 'Invalid request')}",
                    status_code=400,
                    response_data=error_data
                )
            elif response.status_code == 401:
                raise ChapaAPIError(
                    "Unauthorized: Invalid API key",
                    status_code=401
                )
            elif response.status_code == 403:
                raise ChapaAPIError(
                    "Forbidden: Insufficient permissions",
                    status_code=403
                )
            elif response.status_code == 404:
                raise ChapaAPIError(
                    "Not Found: Resource not found",
                    status_code=404
                )
            elif response.status_code == 422:
                error_data = response.json()
                raise ChapaAPIError(
                    f"Validation Error: {error_data.get('message', 'Invalid data')}",
                    status_code=422,
                    response_data=error_data
                )
            elif response.status_code == 429:
                raise ChapaAPIError(
                    "Too Many Requests: Rate limit exceeded",
                    status_code=429
                )
            elif response.status_code >= 500:
                raise ChapaAPIError(
                    f"Chapa Server Error: {response.status_code}",
                    status_code=response.status_code
                )
            else:
                raise ChapaAPIError(
                    f"Unexpected error: {response.status_code}",
                    status_code=response.status_code
                )
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise ChapaAPIError("Request timeout: Could not connect to Chapa")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            raise ChapaAPIError("Connection error: Could not connect to Chapa")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {str(e)}")
            raise ChapaAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {url}: {str(e)}")
            raise ChapaAPIError(f"Invalid response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            raise ChapaAPIError(f"Unexpected error: {str(e)}")
    
    def initialize_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize a payment with Chapa
        
        Args:
            payment_data: Dictionary containing payment details
                Required fields:
                    - amount: Amount in ETB
                    - currency: Currency code (default: ETB)
                    - email: Customer email
                    - first_name: Customer first name
                    - last_name: Customer last name
                    - tx_ref: Unique transaction reference
                Optional fields:
                    - phone_number: Customer phone number
                    - callback_url: Callback URL
                    - return_url: Return URL
                    - customization: Dict with title, description, logo
        
        Returns:
            Dict containing checkout_url and other payment details
        """
        # Validate required fields
        required_fields = ['amount', 'email', 'first_name', 'last_name', 'tx_ref']
        for field in required_fields:
            if field not in payment_data:
                raise ChapaAPIError(f"Missing required field: {field}")
        
        # Set default values
        payment_data.setdefault('currency', 'ETB')
        
        # Prepare request payload
        payload = {
            'amount': str(payment_data['amount']),
            'currency': payment_data['currency'],
            'email': payment_data['email'],
            'first_name': payment_data['first_name'],
            'last_name': payment_data['last_name'],
            'tx_ref': payment_data['tx_ref'],
        }
        
        # Add optional fields if provided
        if 'phone_number' in payment_data:
            payload['phone_number'] = payment_data['phone_number']
        
        if 'callback_url' in payment_data:
            payload['callback_url'] = payment_data['callback_url']
        
        if 'return_url' in payment_data:
            payload['return_url'] = payment_data['return_url']
        
        if 'customization' in payment_data:
            payload['customization'] = payment_data['customization']
        
        # Add metadata if provided
        if 'metadata' in payment_data:
            payload['meta'] = payment_data['metadata']
        
        logger.info(f"Initializing payment with tx_ref: {payment_data['tx_ref']}")
        
        try:
            response = self._make_request('POST', self.INITIALIZE_URL, payload)
            
            # Validate response structure
            if not response.get('status') == 'success':
                raise ChapaAPIError(f"Payment initialization failed: {response.get('message', 'Unknown error')}")
            
            if 'data' not in response or 'checkout_url' not in response['data']:
                raise ChapaAPIError("Invalid response format from Chapa")
            
            return {
                'checkout_url': response['data']['checkout_url'],
                'tx_ref': payment_data['tx_ref'],
                'status': 'pending',
                'message': response.get('message', 'Payment initialized successfully'),
                'response_data': response
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize payment: {str(e)}")
            raise
    
    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify a payment using transaction reference
        """
        if not tx_ref:
            raise ValueError("Transaction reference is required")
        
        verify_url = f"{self.VERIFY_URL}/{tx_ref}"
        logger.info(f"Verifying payment with tx_ref: {tx_ref}")
        
        try:
            response = self._make_request('GET', verify_url)
            
            # Check if status is success
            if response.get('status') != 'success':
                # Payment exists but not successful
                return {
                    'verified': False,
                    'tx_ref': tx_ref,
                    'status': 'pending',
                    'payment_status': 'pending',
                    'message': response.get('message', 'Payment not completed')
                }
            
            if 'data' not in response:
                raise PaymentVerificationError("Invalid response format from Chapa")
            
            data = response['data']
            
            # Map Chapa status to our status
            chapa_status = data.get('status', '').lower()
            status_mapping = {
                'success': 'completed',
                'failed': 'failed',
                'pending': 'pending'
            }
            
            return {
                'verified': chapa_status == 'success',
                'tx_ref': tx_ref,
                'chapa_transaction_id': data.get('id'),
                'amount': float(data.get('amount', 0)),
                'currency': data.get('currency', 'ETB'),
                'status': status_mapping.get(chapa_status, 'pending'),
                'payment_status': chapa_status,
                'customer': {
                    'email': data.get('email'),
                    'name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                },
                'verified_at': data.get('created_at'),
                'response_data': data
            }
            
        except ChapaAPIError as e:
            # Handle 404 - transaction not found on Chapa (not paid yet)
            if e.status_code == 404:
                logger.warning(f"Transaction {tx_ref} not found on Chapa - payment not completed")
                return {
                    'verified': False,
                    'tx_ref': tx_ref,
                    'status': 'pending',
                    'payment_status': 'not_found',
                    'message': 'Payment not yet completed on Chapa'
                }
            raise
        except Exception as e:
            logger.error(f"Failed to verify payment {tx_ref}: {str(e)}")
            raise
        
    def generate_tx_ref(self, prefix: str = "TX") -> str:
        """
        Generate a unique transaction reference for Chapa
        Format: PREFIX-UNIQUE-ID-TIMESTAMP
        """
        unique_id = str(uuid.uuid4()).replace('-', '')[:12].upper()
        timestamp = str(int(timezone.now().timestamp()))[-6:]
        return f"{prefix}-{unique_id}-{timestamp}"


class PaymentService:
    """
    High-level payment service that orchestrates payment operations
    """
    
    def __init__(self):
        self.chapa_client = ChapaClient()
    
    def create_payment(self, order, customer, amount, currency='ETB', metadata=None):
        """
        Create a payment record and initialize with Chapa
        """
        from .models import Payment
        
        # Generate transaction reference
        tx_ref = self.chapa_client.generate_tx_ref()
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            customer=customer,
            amount=amount,
            currency=currency,
            payment_method='chapa',
            tx_ref=tx_ref,
            status='pending',
            metadata=metadata or {}
        )
         
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # Prepare payment data for Chapa
        payment_data = {
            'amount': str(amount),
            'currency': currency,
            'email': customer.email,
            'first_name': customer.first_name or customer.username,
            'last_name': customer.last_name or '',
            'tx_ref': tx_ref,
            'callback_url': self._get_callback_url(),
            'return_url': f"{frontend_url}/order/payment-success?tx_ref={tx_ref}",
            'metadata': {
                'order_id': str(order.id),
                'order_number': order.order_number,
                'customer_id': str(customer.id),
                'payment_id': str(payment.id),
            }
        }
        
        # Add phone number if available
        if customer.phone_number:
            payment_data['phone_number'] = customer.phone_number
        
        # Initialize payment with Chapa
        try:
            result = self.chapa_client.initialize_payment(payment_data)
            
            # Update payment with checkout URL
            payment.checkout_url = result['checkout_url']
            payment.save()
            
            return {
                'payment': payment,
                'checkout_url': result['checkout_url'],
                'tx_ref': tx_ref,
                'status': 'pending'
            }
            
        except Exception as e:
            # Update payment status to failed
            payment.status = 'failed'
            payment.save()
            logger.error(f"Failed to initialize payment: {str(e)}")
            raise
    
    def verify_and_complete_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify payment with Chapa and update payment status
        """
        from .models import Payment
        
        try:
            # Get payment by tx_ref
            try:
                payment = Payment.objects.get(tx_ref=tx_ref)
            except Payment.DoesNotExist:
                raise PaymentVerificationError(f"Payment not found with tx_ref: {tx_ref}")
            
            # Skip if already completed
            if payment.is_paid:
                return {
                    'payment': payment,
                    'verified': True,
                    'status': 'completed',
                    'chapa_transaction_id': payment.chapa_transaction_id,
                    'message': 'Payment already completed'
                }
            
            # Verify with Chapa
            verification_result = self.chapa_client.verify_payment(tx_ref)
            
            # Handle case where payment not found on Chapa (not paid yet)
            if not verification_result.get('verified') and verification_result.get('payment_status') == 'not_found':
                return {
                    'payment': payment,
                    'verified': False,
                    'status': 'pending',
                    'chapa_transaction_id': None,
                    'message': 'Payment not yet completed. Please complete payment on Chapa.',
                    'checkout_url': payment.checkout_url  # Return checkout URL to retry
                }
            
            # Update payment status
            new_status = verification_result.get('status', 'pending')
            payment.status = new_status
            
            if verification_result.get('chapa_transaction_id'):
                payment.chapa_transaction_id = verification_result['chapa_transaction_id']
            
            if payment.is_paid:
                payment.paid_at = timezone.now()
            
            payment.save()
            
            # Update order status if payment completed
            if payment.is_paid and payment.order:
                payment.order.payment_status = True
                payment.order.save()
            
            return {
                'payment': payment,
                'verified': verification_result.get('verified', False),
                'status': new_status,
                'chapa_transaction_id': verification_result.get('chapa_transaction_id'),
                'message': 'Payment verified successfully' if verification_result.get('verified') else 'Payment pending'
            }
            
        except PaymentVerificationError:
            raise
        except ChapaAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify payment {tx_ref}: {str(e)}")
            raise PaymentVerificationError(f"Verification failed: {str(e)}")
        
    def handle_webhook(self, payload: Dict, headers: Dict) -> Dict[str, Any]:
        """
        Handle webhook from Chapa
        """
        from .models import Payment, PaymentWebhook
        
        # Extract event data
        event_type = payload.get('event', '')
        data = payload.get('data', {})
        tx_ref = data.get('tx_ref')
        
        if not tx_ref:
            raise ValueError("No transaction reference in webhook payload")
        
        # Log webhook
        webhook = PaymentWebhook.objects.create(
            event_type=event_type,
            payload=payload,
            headers=headers,
            payment=None  # Will be set after verification
        )
        
        try:
            # Get payment
            try:
                payment = Payment.objects.get(tx_ref=tx_ref)
            except Payment.DoesNotExist:
                webhook.verification_error = f"Payment not found: {tx_ref}"
                webhook.save()
                raise PaymentVerificationError(f"Payment not found: {tx_ref}")
            
            webhook.payment = payment
            webhook.save()
            
            # Handle different event types
            if event_type == 'charge.success':
                # Verify payment
                verification_result = self.chapa_client.verify_payment(tx_ref)
                
                if verification_result['status'] == 'completed':
                    payment.status = 'completed'
                    payment.paid_at = timezone.now()
                    payment.chapa_transaction_id = verification_result.get('chapa_transaction_id')
                    payment.save()
                    
                    # Update order
                    if payment.order:
                        payment.order.payment_status = True
                        payment.order.save()
                    
                    webhook.is_verified = True
                    webhook.processed_at = timezone.now()
                    webhook.save()
                    
                    return {
                        'success': True,
                        'message': 'Payment completed successfully',
                        'payment_id': str(payment.id)
                    }
            
            elif event_type == 'charge.failure':
                payment.status = 'failed'
                payment.save()
                
                webhook.is_verified = True
                webhook.processed_at = timezone.now()
                webhook.save()
                
                return {
                    'success': True,
                    'message': 'Payment failed',
                    'payment_id': str(payment.id)
                }
            
            webhook.is_verified = True
            webhook.processed_at = timezone.now()
            webhook.save()
            
            return {
                'success': True,
                'message': f'Webhook {event_type} processed',
                'payment_id': str(payment.id)
            }
            
        except Exception as e:
            webhook.verification_error = str(e)
            webhook.save()
            logger.error(f"Webhook processing failed: {str(e)}")
            raise
    
    def _get_callback_url(self) -> str:
        """Get callback URL for Chapa"""
        base_url = getattr(settings, 'CHAPA_CALLBACK_URL', '')
        if not base_url:
            base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        return f"{base_url}/api/payments/webhook/"
    
    def _get_return_url(self) -> str:
        """Get return URL for Chapa"""
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{base_url}/order/payment-success"


# Global service instance
payment_service = PaymentService()