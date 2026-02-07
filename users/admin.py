from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_customer', 
                    'is_cafe_staff', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_customer', 'is_cafe_staff', 'is_staff', 'is_active', 
                   'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['activate_users', 'deactivate_users', 'make_cafe_staff', 'remove_cafe_staff']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'is_customer', 'is_cafe_staff', 
                      'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Address Information'), {
            'fields': ('address', 'latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 
                      'password1', 'password2', 
                      'is_customer', 'is_cafe_staff'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('groups')
    
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    
    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    
    @admin.action(description='Make selected users cafe staff')
    def make_cafe_staff(self, request, queryset):
        updated = queryset.update(is_cafe_staff=True)
        self.message_user(request, f'{updated} users marked as cafe staff.')
    
    @admin.action(description='Remove cafe staff status')
    def remove_cafe_staff(self, request, queryset):
        updated = queryset.update(is_cafe_staff=False)
        self.message_user(request, f'{updated} users removed from cafe staff.')