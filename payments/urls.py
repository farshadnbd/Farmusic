# payments/urls.py
from django.urls import path
from .views import (buy_subscription, create_payment, payment_success, payment_history, verify_payment,
                    verify_bitpay_payment)
urlpatterns = [
    path('buy/', buy_subscription, name='buy_subscription'),
    path('create-payment/<int:plan_id>/', create_payment, name='create_payment'),
    path('success/<int:payment_id>/', payment_success, name='payment_success'),
    path('history/', payment_history, name='payment_history'),
    path('verify/', verify_payment, name='verify_payment'),  # کال‌بک زرین‌پال
    path('bitpay/verify/', verify_bitpay_payment, name='bitpay_verify'),  # کال‌بک بیت‌پی
]
