from django.urls import path
from .views import CategoryListAPIView, MenuItemListAPIView, MenuItemDetailAPIView, MenuItemCreateAPIView,MenuItemUpdateDestroyAPIView

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('items/', MenuItemListAPIView.as_view(), name='menu-item-list'),
    path('items/<int:pk>/', MenuItemDetailAPIView.as_view(), name='menu-item-detail'),
    # ✅ ADD THESE TWO LINES
    path('items/create/', MenuItemCreateAPIView.as_view(), name='menu-item-create'),
    path('items/<int:pk>/update/', MenuItemUpdateDestroyAPIView.as_view(), name='menu-item-update'),
]