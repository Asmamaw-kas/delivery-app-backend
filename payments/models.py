import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Payment(models.Model):
    """Model to track payment transactions"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('chapa', 'Chapa'),
        ('cash', 'Cash on Delivery'),
        ('card', 'Card'),
    )
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ETB')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='chapa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Chapa specific fields
    tx_ref = models.CharField(max_length=100, unique=True)  # Chapa transaction reference
    chapa_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_url = models.URLField(blank=True, null=True)  # Chapa checkout URL
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        indexes = [
            models.Index(fields=['tx_ref']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.tx_ref} - {self.amount} {self.currency}"
    
    @property
    def is_paid(self):
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        return self.status == 'failed'

class PaymentWebhook(models.Model):
    """Model to store webhook logs from Chapa"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='webhooks',
        null=True,  # ADD THIS - allows creating webhook before finding payment
        blank=True
    )
    # ... rest stays the same
    # Webhook data
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    headers = models.JSONField(default=dict)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_error = models.TextField(blank=True, null=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = _('payment webhook')
        verbose_name_plural = _('payment webhooks')
    
    def __str__(self):
        return f"Webhook {self.event_type} for {self.payment.tx_ref}"