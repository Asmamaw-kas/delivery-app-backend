from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from menu.models import MenuItem

User = get_user_model()

class Order(models.Model):
    """Order model"""
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('on_the_way', 'On the Way'),  # Changed from 'ongoing' to be more descriptive
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Payment'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(_('order number'), max_length=20, unique=True, editable=False)
    status = models.CharField(_('status'), max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(_('payment method'), max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.BooleanField(_('payment status'), default=False)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2, default=0.00)
    delivery_address = models.TextField(_('delivery address'))
    delivery_latitude = models.DecimalField(_('delivery latitude'), max_digits=13, decimal_places=11, null=True, blank=True)
    delivery_longitude = models.DecimalField(_('delivery longitude'), max_digits=13, decimal_places=11, null=True, blank=True)
    special_instructions = models.TextField(_('special instructions'), blank=True)
    phone_number = models.CharField(_('phone number'), max_length=15)
    delivery_distance = models.FloatField(_('delivery distance'), null=True, blank=True)  # Add this
    delivery_fee = models.DecimalField(_('delivery fee'), max_digits=8, decimal_places=2, default=0.00)  
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)
    prepared_at = models.DateTimeField(_('prepared at'), null=True, blank=True)
    dispatched_at = models.DateTimeField(_('dispatched at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = str(uuid.uuid4())[:13].replace('-', '').upper()
        super().save(*args, **kwargs)
    
    def get_status_progress(self):
        """Get progress percentage based on status"""
        status_weights = {
            'pending': 0,
            'confirmed': 20,
            'preparing': 40,
            'ready': 60,
            'on_the_way': 80,
            'delivered': 100,
            'cancelled': 0,
        }
        return status_weights.get(self.status, 0)

class OrderItem(models.Model):
    """Items within an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    price = models.DecimalField(_('price at time of order'), max_digits=8, decimal_places=2)
    special_request = models.TextField(_('special request'), blank=True)
    
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} for Order #{self.order.order_number}"
    
    def get_total(self):
        return self.quantity * self.price