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

        total = queryset.count()

        for index, music in enumerate(queryset, start=1):

            print(f"[{index}/{total}] {music.title}")

            reason = []

            if music.artist is None:
                reason.append("Artist=None")

            elif music.artist.name.strip().lower() == "unknown artist":
                reason.append("Unknown Artist")

            bad, why = self.check_remote(music.audio_url)

            if bad:
                reason.append(why)

            if reason:
                broken.append((music, " | ".join(reason)))

        print("=" * 80)

        for music, reason in broken:
            print(f"{music.id} | {music.title} | {reason}")

        print("=" * 80)
        print(f"Found {len(broken)} broken musics")

        answer = input("Delete all? (y/N): ")

        if answer.lower() != "y":
            print("Canceled")
            return

        deleted = 0

        for music, reason in broken:

            print(f"Deleting: {music.id} | {music.title}")

            try:
                music.delete()
                deleted += 1
            except Exception as e:
                print(f"ERROR: {e}")

        print("=" * 80)
        print(f"Deleted: {deleted}")
        print("Done")