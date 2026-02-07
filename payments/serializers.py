from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'customer', 'customer_name',
            'amount', 'currency', 'payment_method', 'status',
            'tx_ref', 'checkout_url', 'created_at', 'updated_at',
            'paid_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'customer', 'status', 'tx_ref', 'checkout_url',
            'created_at', 'updated_at', 'paid_at'
        ]


class InitializePaymentSerializer(serializers.Serializer):
    """Serializer for initializing payment"""
    order_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    currency = serializers.CharField(max_length=3, default='ETB')
    return_url = serializers.URLField(required=False)
    
    def validate(self, data):
        # You can add custom validation here
        return data


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification"""
    tx_ref = serializers.CharField(max_length=100, required=True)


class WebhookSerializer(serializers.Serializer):
    """Serializer for webhook payload"""
    event = serializers.CharField(max_length=50)
    data = serializers.DictField()
    
    class Meta:
        fields = ['event', 'data']