from django.contrib import admin
from .models import Payment, PaymentWebhook


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tx_ref', 'customer', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('tx_ref', 'customer__username', 'order__order_number')
    readonly_fields = ('tx_ref', 'chapa_transaction_id', 'checkout_url', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'customer', 'amount', 'currency', 'payment_method', 'status')
        }),
        ('Chapa Details', {
            'fields': ('tx_ref', 'chapa_transaction_id', 'checkout_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ('payment', 'event_type', 'is_verified', 'received_at')
    list_filter = ('event_type', 'is_verified', 'received_at')
    search_fields = ('payment__tx_ref', 'event_type')
    readonly_fields = ('payload', 'headers', 'received_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment', 'event_type', 'is_verified')
        }),
        ('Webhook Data', {
            'fields': ('payload', 'headers'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('received_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Errors', {
            'fields': ('verification_error',),
            'classes': ('collapse',)
        }),
    )