from django.core.management.base import BaseCommand
from django.db.models import Count

from music.models import Music


class Command(BaseCommand):
    help = "Remove duplicate musics"

    def handle(self, *args, **kwargs):

        duplicates = (
            Music.objects
            .values("title", "artist")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        deleted = 0

        for dup in duplicates:

            musics = list(
                Music.objects.filter(
                    title=dup["title"],
                    artist=dup["artist"]
                ).order_by("created_at")
            )

            def score(m):

                return (
                    m.cover is not None or bool(m.cover_url),
                    bool(m.audio_url),
                    m.created_at.timestamp()
                )

            keep = max(musics, key=score)

            for music in musics:

                if music.id != keep.id:
                    print(f"Delete: {music.id} - {music.title}")
                    music.delete()
                    deleted += 1

        print(f"Finished. Deleted {deleted} duplicates.")