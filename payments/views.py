from datetime import timedelta
from django.shortcuts import (render, get_object_or_404, redirect)
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from .models import (SubscriptionPlan, Payment)
from accounts.models import Subscription
import requests


def buy_subscription(request):
    plans = SubscriptionPlan.objects.all()

    return render(request, 'payments/buy_subscription.html', {'plans': plans})


@login_required
def create_payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    payment = Payment.objects.create(user=request.user, plan=plan, amount=plan.price)
    data = {"merchant_id": settings.ZARINPAL_MERCHANT_ID, "amount": payment.amount * 10,
            "callback_url": settings.ZARINPAL_CALLBACK_URL,
            "description": f"خرید اشتراک {plan.title}", }

    response = requests.post(
        "https://api.zarinpal.com/pg/v4/payment/request.json",
        json=data
    )

    result = response.json()

    if ("data" in result and result["data"]["code"] == 100
    ):
        authority = result["data"]["authority"]
        payment.authority = authority
        payment.save()
        return redirect(f"https://www.zarinpal.com/pg/StartPay/{authority}")

    return render(request, "payments/payment-failed.html")


@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.is_paid:
        return redirect('profile')

    payment.is_paid = True
    payment.save()

    expire_date = (timezone.now() + timedelta(days=payment.plan.duration_days))

    subscription, created = (
        Subscription.objects.get_or_create(
            user=request.user,
            defaults={'active': True, 'expire_date': expire_date}))

    if not created:

        if (subscription.active and subscription.expire_date > timezone.now()
        ):
            subscription.expire_date += timedelta(days=payment.plan.duration_days)

        else:
            subscription.expire_date = (timezone.now() + timedelta(days=payment.plan.duration_days))

        subscription.active = True
        subscription.save()

    return redirect('profile')


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'payments/payment_history.html', {'payments': payments})


@login_required
def verify_payment(request):
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if status != "OK":
        return render(request, "payments/payment-failed.html")

    payment = get_object_or_404(Payment, authority=authority, user=request.user)
    data = {"merchant_id": settings.ZARINPAL_MERCHANT_ID, "amount": payment.amount * 10, "authority": authority, }

    response = requests.post(
        "https://api.zarinpal.com/pg/v4/payment/verify.json",
        json=data
    )

    result = response.json()

    if ("data" in result and result["data"]["code"] == 100
    ):

        payment.is_paid = True
        payment.ref_id = str(result["data"]["ref_id"])
        payment.is_paid=True
        payment.save()

        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={"active": True, "expire_date": timezone.now() + timedelta(days=payment.plan.duration_days)}
        )

        if not created:
            if (subscription.expire_date and subscription.expire_date > timezone.now()
            ):
                subscription.expire_date += timedelta(days=payment.plan.duration_days)
            else:
                subscription.expire_date = (timezone.now() + timedelta(days=payment.plan.duration_days))

            subscription.active = True
            subscription.save()

        return render(request, "payments/payment-success.html", {"payment": payment})

    payment.status = "failed"
    payment.save()

    return render(request, "payments/payment-failed.html")
