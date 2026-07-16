import requests
from django.conf import settings
from music.telegram import process_telegram_audio
from music.models import TelegramFile

LAST_UPDATE = 0

def check_updates():
    global LAST_UPDATE

    # 🟢 گرفتن آدرس پروکسی از تنظیمات برای برقراری ارتباط بدون فیلتر در ایران
    api_base = getattr(settings, 'TELEGRAM_API_BASE', 'https://api.telegram.org')
    url = f"{api_base}/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates?offset={LAST_UPDATE + 1}"

    try:
        response = requests.get(url, timeout=20).json()

        if not response.get("ok"):
            print("❌ خطا در دریافت آپدیت‌ها از تلگرام:", response)
            return

        for update in response["result"]:
            LAST_UPDATE = update["update_id"]

            message = update.get("channel_post") or update.get("message")

            if not message:
                continue

            if "audio" in message:
                audio_data = message["audio"]
                file_id = audio_data.get('file_id')

                # چک کردن تکراری بودن قبل از شروع دانلود برای بهینه‌سازی پهنای باند سرور
                if TelegramFile.objects.filter(file_id=file_id).exists():
                    print(f"⛔ آهنگ تکراری است و دانلود نمی‌شود: {audio_data.get('title', '')}")
                    continue

                print("🎵 فایل صوتی جدید تلگرام شناسایی شد. شروع پردازش و دانلود...")
                process_telegram_audio(audio_data)

    except Exception as e:
        print("Polling Error:", e)