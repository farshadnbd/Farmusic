import requests
from django.conf import settings
from music.telegram import process_telegram_audio
from music.models import TelegramFile

LAST_UPDATE = 0

def check_updates():
    global LAST_UPDATE

    api_base = getattr(settings, "TELEGRAM_API_BASE", "https://api.telegram.org", )
    url = (f"{api_base}/bot{settings.TELEGRAM_BOT_TOKEN}"f"/getUpdates?offset={LAST_UPDATE + 1}&timeout=20"
           )

    try:
        response = requests.get(url, timeout=30, ).json()

        if not response.get("ok"):
            print("❌ Telegram Error:", response)
            return

        for update in response.get("result", []):
            LAST_UPDATE = update["update_id"]
            message = (update.get("channel_post") or update.get("message"))

            if not message:
                continue

            audio = message.get("audio")

            if not audio:
                continue

            file_id = audio["file_id"]

            if TelegramFile.objects.filter(file_id=file_id).exists():
                print(f"⛔ Duplicate: {audio.get('title', '')}")
                continue

            print(f"🎵 New Telegram Music: {audio.get('title', '')}")
            process_telegram_audio(audio)
    except Exception as e:
        print("Polling Error:", e)