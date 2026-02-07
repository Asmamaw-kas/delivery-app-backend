from rest_framework import serializers
from .models import UserAddress

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserAddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('address_type', 'label', 'full_address', 
                 'latitude', 'longitude', 'apartment', 
                 'building', 'floor', 'notes')