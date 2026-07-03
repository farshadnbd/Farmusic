from django.contrib import admin
from .models import SubscriptionPlan, Payment


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'price',
        'duration_days'
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'plan',
        'amount',
        'is_paid',
        'created_at'
    ]

    list_filter = [
        'is_paid'
    ]