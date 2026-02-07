from django.contrib import admin
from .models import Category, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'created_at', 'updated_at')
    list_filter = ('category_type', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 20

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'preparation_time', 'created_at')
    list_filter = ('is_available', 'category', 'category__category_type', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available', 'preparation_time')
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available', 'preparation_time')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('category')
        return queryset