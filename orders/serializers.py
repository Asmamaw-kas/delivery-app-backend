from rest_framework import serializers
from .models import Order, OrderItem
from menu.serializers import MenuItemSerializer
from users.serializers import UserSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_details = MenuItemSerializer(source='menu_item', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_details = UserSerializer(source='customer', read_only=True)
    status_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_number', 'created_at', 'total_amount')
    
    def get_status_progress(self, obj):
        return obj.get_status_progress()
    
    def create(self, validated_data):
        # Handle order creation with items
        items_data = self.context['request'].data.get('items', [])
        order = Order.objects.create(**validated_data)
        
        # Calculate total amount
        total = 0
        for item_data in items_data:
            menu_item_id = item_data.get('menu_item')
            quantity = item_data.get('quantity', 1)
            menu_item = order.menu_item.objects.get(id=menu_item_id)
            item_total = menu_item.price * quantity
            total += item_total
            
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                price=menu_item.price,
                special_request=item_data.get('special_request', '')
            )
        
        order.total_amount = total
        order.save()
        return order

class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    delivery_address = serializers.CharField(max_length=500)
    delivery_latitude = serializers.DecimalField(max_digits=13, decimal_places=11)
    delivery_longitude = serializers.DecimalField(max_digits=13, decimal_places=11)
    special_instructions = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15)
    delivery_distance = serializers.FloatField(required=False , allow_null=True)  # Add this
    delivery_fee = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHODS)
  