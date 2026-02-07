from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from .services import payment_service
import logging

logger = logging.getLogger(__name__)

@shared_task
def verify_pending_payments():
    """
    Background task to verify pending payments
    Runs every 5 minutes
    """
    try:
        # Find payments that are pending for more than 10 minutes
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        pending_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=ten_minutes_ago,
            payment_method='chapa'
        )[:20]  # Limit to 20 at a time
        
        for payment in pending_payments:
            try:
                result = payment_service.chapa_client.verify_payment(payment.tx_ref)
                
                if result['verified']:
                    payment.status = result['status']
                    payment.chapa_transaction_id = result.get('chapa_transaction_id')
                    
                    if result['status'] == 'completed':
                        payment.paid_at = timezone.now()
                        # Update order
                        if payment.order:
                            payment.order.payment_status = True
                            payment.order.save()
                    
                    payment.save()
                    logger.info(f"Verified payment {payment.tx_ref}: {result['status']}")
                    
            except Exception as e:
                logger.error(f"Failed to verify payment {payment.tx_ref}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in verify_pending_payments task: {str(e)}")