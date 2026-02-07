from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserAddress
from .serializers import UserAddressSerializer, UserAddressCreateSerializer

class UserAddressListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['address_type', 'is_default']
    
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserAddressCreateSerializer
        return UserAddressSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserAddressDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

class SetDefaultAddressAPIView(generics.UpdateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_default = True
        instance.save()
        return Response({'message': 'Address set as default successfully'})