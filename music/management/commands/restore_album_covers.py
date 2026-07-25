from django.core.management.base import BaseCommand
from music.models import Album


class Command(BaseCommand):
    help = "Restore album covers from music covers"

    def handle(self, *args, **kwargs):

        restored = 0

        albums = Album.objects.filter(
            cover_url__isnull=True
        )

        for album in albums:

            music = (
                album.music_set
                .exclude(cover_url__isnull=True)
                .exclude(cover_url="")
                .order_by("track_number", "id")
                .first()
            )

            if not music:
                print(f"Skip: {album.title}")
                continue

            album.cover_url = music.cover_url
            album.save(update_fields=["cover_url"])

            restored += 1
            print(f"✔ Restored: {album.title}")

        print("=" * 50)
        print(f"Restored albums: {restored}")