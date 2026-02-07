from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('initialize/', views.InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify/<str:tx_ref>/', views.VerifyPaymentView.as_view(), name='verify-payment'),
    path('<uuid:id>/', views.PaymentStatusView.as_view(), name='payment-status'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    
    # Webhook endpoint (CSRF exempt)
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
]