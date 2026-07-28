import json
import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .telegram import process_telegram_audio


@csrf_exempt
@require_POST
def telegram_webhook(request):
    print("✅ WEBHOOK HIT")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        message = payload.get("message") or payload.get("channel_post")

        if not message:
            return JsonResponse({"status": "no message"}, status=200)

        if "audio" not in message:
            return JsonResponse({"status": "no audio"}, status=200)

        audio_data = message["audio"]
        print(f"🎵 New Telegram Audio: "f"{audio_data.get('title')} | "f"{audio_data.get('file_name')}")

        # اجرای پردازش در بک‌گراند
        threading.Thread(target=process_telegram_audio, args=(audio_data,), daemon=True, ).start()

        # پاسخ فوری به تلگرام
        return JsonResponse({"status": "accepted"}, status=200)

    except json.JSONDecodeError:
        print("❌ Invalid JSON")
        return JsonResponse({"error": "invalid json"}, status=400)

    except Exception as e:
        print("❌ Webhook Error:", e)
        return JsonResponse({"error": "internal server error"}, status=500)
