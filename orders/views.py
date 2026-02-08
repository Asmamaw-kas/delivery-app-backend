from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from menu.models import MenuItem
from django.db.models import Count, Sum, Avg, F, Q
from users.models import User
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class CafeOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'payment_status']
    search_fields = ['order_number', 'customer__username', 'customer__email', 'phone_number']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Order.objects.all().select_related('customer').prefetch_related('items')

class CafeOrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Order.objects.all().select_related('customer').prefetch_related('items')


class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method', 'payment_status']
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)
    
    def create(self, request, *args, **kwargs):
        create_serializer = OrderCreateSerializer(data=request.data)
        if create_serializer.is_valid():
            # Create order with user instance, not just ID
            order_data = {
                'customer': request.user,  # Pass the User instance
                'delivery_address': create_serializer.validated_data['delivery_address'],
                'delivery_latitude': create_serializer.validated_data['delivery_latitude'],
                'delivery_longitude': create_serializer.validated_data['delivery_longitude'],
                'special_instructions': create_serializer.validated_data.get('special_instructions', ''),
                'phone_number': create_serializer.validated_data['phone_number'],
                'payment_method': create_serializer.validated_data['payment_method'],
            }
            
            # Create order first
            order = Order.objects.create(**order_data)
            
            # Calculate total and create order items
            total = 0
            items_data = request.data.get('items', [])
            
            for item_data in items_data:
                menu_item_id = item_data.get('menu_item')
                quantity = item_data.get('quantity', 1)
                
                try:
                    menu_item = MenuItem.objects.get(id=menu_item_id)
                    item_total = menu_item.price * quantity
                    total += item_total
                    
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        price=menu_item.price,
                        special_request=item_data.get('special_request', '')
                    )
                except MenuItem.DoesNotExist:
                    # If menu item doesn't exist, delete the order and return error
                    order.delete()
                    return Response(
                        {'error': f'Menu item with ID {menu_item_id} does not exist'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except ValueError as e:
                    order.delete()
                    return Response(
                        {'error': f'Invalid data for menu item {menu_item_id}: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update order total
            order.total_amount = total
            order.save()
            
            # Return serialized order
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        status_action = request.data.get('action')
        
        if status_action == 'confirm_delivery' and instance.status == 'on_the_way':
            instance.status = 'delivered'
            instance.delivered_at = timezone.now()
            instance.save()
            return Response({'message': 'Delivery confirmed successfully'})
        
        elif status_action == 'cancel' and instance.status in ['pending', 'confirmed']:
            instance.status = 'cancelled'
            instance.cancelled_at = timezone.now()
            instance.save()
            return Response({'message': 'Order cancelled successfully'})
        
        return Response({'error': 'Invalid action for current order status'}, 
                       status=status.HTTP_400_BAD_REQUEST)

class CafeOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method', 'payment_status']
    
    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')

class CafeOrderUpdateAPIView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Order.objects.all()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Order.ORDER_STATUS):
            # Update timestamps based on status
            if new_status == 'confirmed':
                instance.confirmed_at = timezone.now()
            elif new_status == 'preparing':
                instance.prepared_at = timezone.now()
            elif new_status == 'on_the_way':
                instance.dispatched_at = timezone.now()
            
            instance.status = new_status
            instance.save()
            return Response(OrderSerializer(instance).data)
        
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    try:
        # Calculate basic stats
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(
            status__in=['pending', 'confirmed', 'preparing', 'ready', 'on_the_way']
        ).count()
        total_users = User.objects.count()
        
        # Menu items count by category type
        total_foods = MenuItem.objects.filter(category__category_type='food').count()
        total_drinks = MenuItem.objects.filter(category__category_type='drink').count()
        
        # Revenue calculation
        delivered_orders = Order.objects.filter(status='delivered')
        total_revenue = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        avg_order_value = delivered_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Delivered today
        today = timezone.now().date()
        delivered_today = delivered_orders.filter(
            delivered_at__date=today
        ).count()
        
        # Recent orders with customer details
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
        
        # Top products - FIXED: Calculate revenue correctly
        top_products = OrderItem.objects.select_related(
            'menu_item',
            'menu_item__category'
        ).values(
            'menu_item__id',
            'menu_item__name',
            'menu_item__category__category_type'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))  # FIXED: Multiply price by quantity
        ).order_by('-total_sold')[:5]
        
        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_users': total_users,
            'total_foods': total_foods,
            'total_drinks': total_drinks,
            'total_revenue': float(total_revenue),
            'average_order_value': float(avg_order_value),
            'delivered_today': delivered_today,
            'recent_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer': order.customer.username if order.customer else 'Guest',
                    'customer_email': order.customer.email if order.customer else '',
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at.isoformat(),
                }
                for order in recent_orders
            ],
            'top_products': [
                {
                    'id': item['menu_item__id'],
                    'name': item['menu_item__name'] or 'Unknown',
                    'type': item['menu_item__category__category_type'] or 'unknown',
                    'sales_count': item['total_sold'] or 0,
                    'revenue': float(item['total_revenue'] or 0),
                }
                for item in top_products
            ]
        }
        
        return Response(stats, status=200)
        
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"❌ Dashboard stats error: {str(e)}")
        print(traceback.format_exc())
        
        # Return error with default values
        return Response({
            'error': str(e),
            'total_orders': 0,
            'pending_orders': 0,
            'total_users': 0,
            'total_foods': 0,
            'total_drinks': 0,
            'total_revenue': 0.0,
            'average_order_value': 0.0,
            'delivered_today': 0,
            'recent_orders': [],
            'top_products': []
        }, status=200)  # Still return 200 so frontend doesn't break
        
        
@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_data(request):
    time_range = request.GET.get('time_range', 'week')
    
    # Calculate time range
    now = timezone.now()
    if time_range == 'day':
        start_date = now - timedelta(days=1)
    elif time_range == 'week':
        start_date = now - timedelta(days=7)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    elif time_range == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=7)
    
    # Generate date labels
    date_labels = []
    current_date = start_date
    while current_date <= now:
        date_labels.append(current_date.strftime('%b %d'))
        current_date += timedelta(days=1)
    
    # Get revenue data
    revenue_data = []
    orders_data = []
    
    # This is a simplified version - you'd want to aggregate by day
    orders = Order.objects.filter(created_at__gte=start_date, status='delivered')
    revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # For demo, distribute evenly across days
    days = (now - start_date).days + 1
    daily_revenue = revenue / days if days > 0 else 0
    daily_orders = orders.count() / days if days > 0 else 0
    
    for _ in range(days):
        revenue_data.append(float(daily_revenue))
        orders_data.append(int(daily_orders))
    
    analytics = {
        'date_labels': date_labels,
        'revenue_data': revenue_data,
        'orders_data': orders_data,
        'total_revenue': float(revenue),
        'total_orders': orders.count(),
        'average_order_value': float(orders.aggregate(avg=Avg('total_amount'))['avg'] or 0),
    }
    
    return Response(analytics)

    