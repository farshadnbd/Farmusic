from django.db import models
from django.contrib.auth.models import User


class SubscriptionPlan(models.Model):
    title = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField()

    def __str__(self):
        return self.title


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    authority = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
