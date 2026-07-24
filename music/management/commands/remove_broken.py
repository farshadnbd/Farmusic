from django.core.management.base import BaseCommand
from music.models import Music
import requests


class Command(BaseCommand):
    help = "Remove broken musics"

    def broken_audio(self, url):
        if not url:
            return True, "No audio_url"

        try:
            r = requests.head(url, timeout=10, allow_redirects=True)

            if r.status_code != 200:
                return True, f"HTTP {r.status_code}"

            size = int(r.headers.get("Content-Length", 0))

            if size == 0:
                return True, "0 Byte"

            return False, ""

        except Exception as e:
            return True, str(e)

    def handle(self, *args, **kwargs):

        broken = []

        for music in Music.objects.select_related("artist"):

            reason = None

            # آرتیست نامعتبر
            if music.artist is None:
                reason = "Artist=None"

            elif music.artist.name.lower() == "unknown artist":
                reason = "Unknown Artist"

            # فایل خراب
            bad, why = self.broken_audio(music.audio_url)

            if bad:
                reason = why

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
            print("Delete:", music.id, music.title)
            music.delete()

        print("Done")