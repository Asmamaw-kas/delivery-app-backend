from django.urls import path
from . import views
from .views import dashboard_stats, analytics_data
from .views import (OrderListCreateAPIView, OrderDetailAPIView, 
                   OrderStatusUpdateAPIView, CafeOrderListAPIView,
                   CafeOrderUpdateAPIView, CafeOrderListAPIView, CafeOrderDetailAPIView)

urlpatterns = [
    # Customer endpoints
    path('', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
    path('admin/dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    path('admin/analytics/', analytics_data, name='analytics'),
    
    # Cafe staff endpoints
    path('cafe/all/', CafeOrderListAPIView.as_view(), name='cafe-order-list'),
    path('cafe/<int:pk>/update/', CafeOrderUpdateAPIView.as_view(), name='cafe-order-update'),
]