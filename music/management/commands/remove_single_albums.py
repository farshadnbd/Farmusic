from django.core.management.base import BaseCommand
from music.models import Album


class Command(BaseCommand):
    help = "Remove useless single-track albums"

    def handle(self, *args, **kwargs):

        deleted = 0

        for album in Album.objects.all():

            # فقط آلبوم‌های تک‌آهنگی
            if album.music_set.count() != 1:
                continue

            music = album.music_set.first()

            album_title = album.title.strip().lower()
            music_title = music.title.strip().lower()

            remove = False

            # اگر Single بود
            if "single" in album_title:
                remove = True

            # یا اسم آلبوم و آهنگ یکی بود
            elif album_title == music_title:
                remove = True

            if not remove:
                continue

            music.album = None
            music.save(update_fields=["album"])

            print(f"Delete Album: {album.id} - {album.title}")

            album.delete()
            deleted += 1

        print(f"\nDeleted {deleted} albums")