from rest_framework import serializers
from .models import Category, MenuItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# menu/serializers.py

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'category', 
            'category_name', 'category_type', 'image', 
            'preparation_time', 'is_available', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'image': {'required': False},  # ✅ Make image optional for updates
        }

class MenuItemSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'price', 'image')