from django.urls import path
from .views import CategoryListAPIView, MenuItemListAPIView, MenuItemDetailAPIView

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),
    path('items/<int:pk>/', MenuItemDetailAPIView.as_view(), name='menu-item-detail'),
]