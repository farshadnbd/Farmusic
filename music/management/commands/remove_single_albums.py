from django.core.management.base import BaseCommand
from music.models import Album


class Command(BaseCommand):
    help = "Remove single albums"

    def handle(self, *args, **kwargs):

        deleted = 0

        albums = Album.objects.all()

        for album in albums:

            if album.music_set.count() != 1:
                continue

            if "single" not in album.title.lower():
                continue

            music = album.music_set.first()

            music.album = None
            music.save(update_fields=["album"])

            print(f"Delete Album: {album.id} - {album.title}")

            album.delete()
            deleted += 1

        print(f"\nDeleted {deleted} albums")