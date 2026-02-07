from django.urls import path
from .views import (UserAddressListCreateAPIView, UserAddressDetailAPIView,
                   SetDefaultAddressAPIView)

urlpatterns = [
    path('', UserAddressListCreateAPIView.as_view(), name='address-list-create'),
    path('<int:pk>/', UserAddressDetailAPIView.as_view(), name='address-detail'),
    path('<int:pk>/set-default/', SetDefaultAddressAPIView.as_view(), name='set-default-address'),
]