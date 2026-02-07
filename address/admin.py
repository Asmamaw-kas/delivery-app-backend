from django.contrib import admin
from .models import UserAddress

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address_type', 'is_default', 
                    'full_address_truncated', 'created_at')
    list_filter = ('address_type', 'is_default', 'created_at')
    search_fields = ('user__username', 'user__email', 'full_address', 
                     'label', 'apartment', 'building')
    list_editable = ('is_default',)
    list_per_page = 25
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Address Details', {
            'fields': (('address_type', 'label'), 
                      'full_address', 
                      ('latitude', 'longitude'))
        }),
        ('Additional Details', {
            'fields': (('apartment', 'building', 'floor'),
                      'notes'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_default',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def full_address_truncated(self, obj):
        if len(obj.full_address) > 50:
            return obj.full_address[:47] + '...'
        return obj.full_address
    full_address_truncated.short_description = 'Full Address'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset