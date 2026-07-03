import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .telegram import process_telegram_audio
@csrf_exempt
@require_POST
def telegram_webhook(request):
    print("WEBHOOK HIT")
    """ویو اختصاصی برای دریافت بروزرسانی‌ها و آهنگ‌ها از ربات تلگرام"""
    try:
        # ۱. دریافت داده‌های ارسالی از تلگرام
        payload = json.loads(request.body.decode('utf-8'))

        # ۲. بررسی اینکه پیام حاوی فایل صوتی (audio) است یا خیر
        message = payload.get("message") or payload.get("channel_post")
        if not message:
            return JsonResponse({"status": "no message"})
        print(json.dumps(payload, indent=4))
        # اگر پیام مستقیم صوتی بود، یا فایلی بود که فوروارد شده بود
        if 'audio' in message:
            audio_data = message['audio']

            # ارسال اطلاعات فایل به تابع پردازش در telegram.py
            success = process_telegram_audio(audio_data)

            if success:
                return JsonResponse({'status': 'processed successfully'}, status=200)
            else:
                return JsonResponse({'status': 'failed to process audio'}, status=500)

        return JsonResponse({'status': 'no audio found in message'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print("Webhook View Error:", e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)