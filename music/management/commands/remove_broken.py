from django.core.management.base import BaseCommand
from music.models import Music
import requests


class Command(BaseCommand):
    help = "Find musics whose audio file does not exist on download host"

    def check_remote(self, url):
        if not url:
            return True, "No audio_url"

        try:
            response = requests.head(
                url,
                timeout=5,
                allow_redirects=True,
            )

            if response.status_code != 200:
                return True, f"HTTP {response.status_code}"

            size = int(response.headers.get("Content-Length", 0))

            if size == 0:
                return True, "0 Byte"

            return False, ""

        except Exception as e:
            return True, str(e)

    def handle(self, *args, **kwargs):

        broken = []

        queryset = Music.objects.select_related("artist")

        print(f"Checking {queryset.count()} musics...")

        for music in queryset:

            reason = None

            # همیشه فایل را بررسی کن
            bad, why = self.check_remote(music.audio_url)

            if music.artist is None:
                reason = "Artist=None"

            elif music.artist.name.strip().lower() == "unknown artist":
                reason = "Unknown Artist"

            elif not music.audio_url:
                reason = "No audio_url"

            elif bad:
                reason = why

            if reason:
                broken.append((music, reason))

        print("=" * 80)

        for music, reason in broken:
            artist = music.artist.name if music.artist else "None"

            print(
                f"{music.id} | {artist} | {music.title} | {reason}"
            )

        print("=" * 80)
        print(f"Found {len(broken)} broken musics")

        answer = input("Delete all? (y/N): ")

        if answer.lower() != "y":
            print("Canceled")
            return

        deleted = 0

        for music, reason in broken:

            print(f"Deleting -> {music.id} | {music.title}")

            try:
                music.delete()
                deleted += 1

            except Exception as e:
                print(f"ERROR {music.id}: {e}")

        print("=" * 80)
        print(f"Deleted: {deleted}")
        print("Done")