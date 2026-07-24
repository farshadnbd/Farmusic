from django.core.management.base import BaseCommand
from music.models import Music
import requests


class Command(BaseCommand):
    help = "Find and remove broken musics"

    def check_remote(self, url):
        if not url:
            return True, "No audio_url"

        try:
            r = requests.get(
                url,
                stream=True,
                timeout=(3, 5),
                allow_redirects=True,
            )

            if r.status_code != 200:
                return True, f"HTTP {r.status_code}"

            size = int(r.headers.get("Content-Length", 0))
            r.close()

            if size == 0:
                return True, "0 Byte"

            return False, ""

        except Exception as e:
            return True, str(e)

    def handle(self, *args, **kwargs):

        broken = []

        queryset = Music.objects.select_related("artist")

        for music in queryset:

            reason = None

            # آرتیست نامعتبر
            if music.artist is None:
                reason = "Artist=None"

            elif music.artist.name.strip().lower() == "unknown artist":
                reason = "Unknown Artist"

            # فقط اگر قبلاً مشکوک بود، فایل را چک کن
            if reason:
                bad, why = self.check_remote(music.audio_url)

                if bad:
                    reason += f" | {why}"

            # اگر URL اصلاً وجود ندارد
            elif not music.audio_url:
                reason = "No audio_url"

            if reason:
                broken.append((music, reason))

        print("=" * 80)

        for music, reason in broken:
            print(f"{music.id} | {music.title} | {reason}")

        print("=" * 80)
        print(f"Found {len(broken)} broken musics")

        answer = input("Delete all? (y/N): ")

        if answer.lower() != "y":
            print("Canceled")
            return

        for music, reason in broken:
            print("Deleting:", music.id, music.title)
            music.delete()

        print("Done")