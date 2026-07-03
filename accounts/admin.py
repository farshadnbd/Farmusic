from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'active',
        'expire_date'
    ]

    list_filter = [
        'active'
    ]
