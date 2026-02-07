import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Payment
from orders.models import Order
from .serializers import (
    PaymentSerializer,
    InitializePaymentSerializer,
    PaymentVerificationSerializer,
    WebhookSerializer
)
from .services import payment_service
from .exceptions import PaymentError, ChapaAPIError, PaymentVerificationError

logger = logging.getLogger(__name__)


class InitializePaymentView(generics.CreateAPIView):
    """
    Initialize a payment with Chapa
    POST /api/payments/initialize/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InitializePaymentSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get order
            order = get_object_or_404(
                Order, 
                id=serializer.validated_data['order_id'],
                customer=request.user
            )
            
            # Check if payment already exists
            existing_payment = Payment.objects.filter(
                order=order,
                status__in=['pending', 'processing', 'completed']
            ).first()
            
            if existing_payment:
                if existing_payment.is_paid:
                    return Response({
                        'error': 'Payment already completed',
                        'payment_id': str(existing_payment.id)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if existing_payment.checkout_url:
                    return Response({
                        'checkout_url': existing_payment.checkout_url,
                        'tx_ref': existing_payment.tx_ref,
                        'payment_id': str(existing_payment.id),
                        'message': 'Payment already initialized'
                    })
            
            # Create payment
            amount = serializer.validated_data['amount']
            currency = serializer.validated_data.get('currency', 'ETB')
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

            result = payment_service.create_payment(
                order=order,
                customer=request.user,
                amount=amount,
                currency=currency,
                metadata={
                    'return_url': serializer.validated_data.get('return_url') or f"{frontend_url}/order/payment-success",
                    'ip_address': self._get_client_ip(request)
                }
            )
            
            return Response({
                'checkout_url': result['checkout_url'],
                'tx_ref': result['tx_ref'],
                'payment_id': str(result['payment'].id),
                'message': 'Payment initialized successfully',
                'status': 'pending'
            })
            
        except ChapaAPIError as e:
            logger.error(f"Chapa API error: {str(e)}")
            return Response({
                'error': 'Payment initialization failed',
                'message': str(e),
                'status_code': e.status_code if hasattr(e, 'status_code') else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except PaymentError as e:
            logger.error(f"Payment error: {str(e)}")
            return Response({
                'error': 'Payment failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tx_ref):
        try:
            payment = get_object_or_404(
                Payment,
                tx_ref=tx_ref,
                customer=request.user
            )
            
            result = payment_service.verify_and_complete_payment(tx_ref)
            payment.refresh_from_db()
            
            serializer = PaymentSerializer(payment)
            
            response_data = {
                'verified': result['verified'],
                'status': result['status'],
                'message': result.get('message'),
                'payment': serializer.data
            }
            
            # Include checkout_url if payment not completed (for retry)
            if not result['verified'] and result.get('checkout_url'):
                response_data['checkout_url'] = result['checkout_url']
            
            # Return 200 even for pending - it's not an error
            return Response(response_data)
            
        except PaymentVerificationError as e:
            return Response({
                'error': 'Verification failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except ChapaAPIError as e:
            logger.error(f"Chapa API error: {str(e)}")
            return Response({
                'error': 'Payment gateway error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Verification error: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentStatusView(generics.RetrieveAPIView):
    """
    Get payment status
    GET /api/payments/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        return Payment.objects.filter(customer=self.request.user)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(APIView):
    """
    Handle Chapa webhooks
    POST /api/payments/webhook/
    """
    permission_classes = []  # No authentication for webhooks
    authentication_classes = []  # No authentication for webhooks
    
    def post(self, request):
        logger.info(f"Received Chapa webhook: {request.data}")
        
        try:
            # Process webhook
            result = payment_service.handle_webhook(
                payload=request.data,
                headers=dict(request.headers)
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return Response({
                'error': 'Webhook processing failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _verify_webhook_signature(self, request):
        """
        Verify webhook signature if Chapa provides one
        This is a placeholder - check Chapa documentation for signature verification
        """
        # Chapa might send a signature in headers
        # signature = request.headers.get('Chapa-Signature')
        # if not signature:
        #     raise ValueError("No signature in webhook")
        
        # Implement signature verification based on Chapa documentation
        pass


class PaymentHistoryView(generics.ListAPIView):
    """
    Get user's payment history
    GET /api/payments/history/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(
            customer=self.request.user
        ).select_related('order').order_by('-created_at')