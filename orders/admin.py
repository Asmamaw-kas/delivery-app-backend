from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'get_total')
    fields = ('menu_item', 'quantity', 'price', 'special_request', 'get_total')
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'total_amount', 
                    'payment_method', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 
                   'created_at')
    search_fields = ('order_number', 'customer__username', 'customer__email',
                     'delivery_address', 'phone_number')
    list_editable = ('status', 'payment_status')
    list_per_page = 30
    readonly_fields = ('order_number', 'created_at', 'total_amount', 
                      'confirmed_at', 'prepared_at', 'dispatched_at',
                      'delivered_at', 'cancelled_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'total_amount')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_latitude', 
                      'delivery_longitude', 'phone_number')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Instructions & Notes', {
            'fields': ('special_instructions',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (('created_at', 'confirmed_at'),
                      ('prepared_at', 'dispatched_at'),
                      ('delivered_at', 'cancelled_at')),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('customer')
        return queryset
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price', 'get_total')
    list_filter = ('order__status',)  # Removed 'created_at' from here
    search_fields = ('order__order_number', 'menu_item__name')
    list_per_page = 50
    readonly_fields = ('price', 'get_total')
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('order', 'menu_item')
        return queryset