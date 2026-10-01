# payments/views.py

from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from .models import SubscriptionPlan, Payment
from accounts.models import Subscription
import requests


def buy_subscription(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'payments/buy_subscription.html', {'plans': plans})


@login_required
def create_payment(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    gateway = request.GET.get('gateway', 'zarinpal')  # دریافت نوع درگاه انتخابی

    payment = Payment.objects.create(user=request.user,plan=plan,amount=plan.price,gateway=gateway)

    # ------------------ درگاه بیت‌پی ------------------
    if gateway == 'bitpay':
        data = {
            'api': settings.BITPAY_API_KEY,
            'redirect': settings.BITPAY_CALLBACK_URL,
            "amount": payment.amount * 10,  # تبدیل تومان به ریال
            'factorId': payment.id,
            'name': request.user.username,
            'email': request.user.email or '',
            'description': f"خرید اشتراک {plan.title}"
        }

        try:
            response = requests.post('https://bitpay.ir/payment/gateway-send', data=data, timeout=15)
            id_get = response.text.strip()

            if id_get.isdigit() and int(id_get) > 0:
                payment.trans_id = id_get
                payment.save(update_fields=['trans_id'])
                return redirect(f'https://bitpay.ir/payment/gateway-{id_get}-get')
            else:
                payment.status = 'failed'
                payment.save()
                return render(request, "payments/payment-failed.html")

        except Exception as e:
            print("BitPay Request Error:", e)
            payment.status = 'failed'
            payment.save()
            return render(request, "payments/payment-failed.html")

    # ------------------ درگاه زرین‌پال ------------------
    else:
        data = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": payment.amount * 10,  # تبدیل تومان به ریال
            "callback_url": settings.ZARINPAL_CALLBACK_URL,
            "description": f"خرید اشتراک {plan.title}",
        }

        # 👈 اضافه کردن هدرهای ضروری برای شاپرک
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Referer": "https://farmusic.ir"
        }

        try:
            response = requests.post(
                "https://api.zarinpal.com/pg/v4/payment/request.json",
                json=data,
                headers=headers,  # 👈 ارسال هدرها
                timeout=15
            )
            result = response.json()

            if "data" in result and result["data"]["code"] == 100:
                authority = result["data"]["authority"]
                payment.authority = authority
                payment.save(update_fields=['authority'])
                return redirect(f"https://www.zarinpal.com/pg/StartPay/{authority}")

        except Exception as e:
            print("Zarinpal Request Error:", e)

        payment.status = 'failed'
        payment.save()
        return render(request, "payments/payment-failed.html")


@login_required
def verify_payment(request):
    """تایید پرداخت زرین‌پال"""
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if status != "OK":
        return render(request, "payments/payment-failed.html")

    payment = get_object_or_404(Payment, authority=authority, user=request.user)
    data = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": payment.amount * 10,
        "authority": authority,
    }

    response = requests.post(
        "https://api.zarinpal.com/pg/v4/payment/verify.json",
        json=data
    )
    result = response.json()

    if "data" in result and result["data"]["code"] == 100:
        payment.is_paid = True
        payment.ref_id = str(result["data"]["ref_id"])
        payment.status = 'success'
        payment.save()

        # فعال‌سازی یا تمدید اشتراک
        activate_or_renew_subscription(request.user, payment.plan)

        return render(request, "payments/payment-success.html", {"payment": payment})

    payment.status = "failed"
    payment.save()
    return render(request, "payments/payment-failed.html")


def verify_bitpay_payment(request):
    """تایید پرداخت بیت‌پی"""
    trans_id = request.POST.get('trans_id') or request.GET.get('trans_id')
    id_get = request.POST.get('id_get') or request.GET.get('id_get')

    if not trans_id or not id_get:
        return render(request, "payments/payment-failed.html")

    data = {
        'api': settings.BITPAY_API_KEY,
        'trans_id': trans_id,
        'id_get': id_get,
        'json': 1
    }

    try:
        response = requests.post('https://bitpay.ir/payment/gateway-result-second', data=data, timeout=15)
        result = response.json()

        if result.get('status') == 1:
            factor_id = result.get('factorId')
            payment = get_object_or_404(Payment, id=factor_id)

            if not payment.is_paid:
                payment.is_paid = True
                payment.ref_id = str(trans_id)
                payment.status = 'success'
                payment.save()

                # فعال‌سازی یا تمدید اشتراک
                activate_or_renew_subscription(payment.user, payment.plan)

            return render(request, "payments/payment-success.html", {"payment": payment})

    except Exception as e:
        print("BitPay Verify Error:", e)

    return render(request, "payments/payment-failed.html")


def activate_or_renew_subscription(user, plan):
    """تابع کمکی جهت افزایش یا فعال‌سازی اشتراک"""
    subscription, created = Subscription.objects.get_or_create(
        user=user,
        defaults={"active": True, "expire_date": timezone.now() + timedelta(days=plan.duration_days)}
    )

    if not created:
        if subscription.expire_date and subscription.expire_date > timezone.now():
            subscription.expire_date += timedelta(days=plan.duration_days)
        else:
            subscription.expire_date = timezone.now() + timedelta(days=plan.duration_days)

        subscription.active = True
        subscription.save()


@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payments/payment-success.html', {'payment': payment})


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_history.html', {'payments': payments})