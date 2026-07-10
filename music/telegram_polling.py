import requests
from django.conf import settings
from music.telegram import process_telegram_audio
from music.models import TelegramFile  # 🟢 اضافه کردن مدل فایل‌ها

LAST_UPDATE = 0

def check_updates():
    global LAST_UPDATE

    url = (
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
        f"/getUpdates?offset={LAST_UPDATE + 1}"
    )

    try:
        response = requests.get(
            url,
            proxies=PROXIES,
            timeout=20
        ).json()

        if not response["ok"]:
            return

        for update in response["result"]:
            LAST_UPDATE = update["update_id"]

            message = (
                update.get("channel_post")
                or update.get("message")
            )

            if not message:
                continue

            if "audio" in message:
                audio_data = message["audio"]
                file_id = audio_data.get('file_id') # 🟢 گرفتن آیدی فایل

                # 🟢 چک کردن تکراری بودن قبل از شروع دانلود
                if TelegramFile.objects.filter(file_id=file_id).exists():
                    print(f"⛔ آهنگ تکراری است و دانلود نمی‌شود: {audio_data.get('title', '')}")
                    continue

                print("🎵 New Telegram Audio Detected. Starting download...")
                process_telegram_audio(audio_data)

    except Exception as e:
        print("Polling Error:", e)