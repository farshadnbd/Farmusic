import os
import tempfile
import requests
from django.core.management.base import BaseCommand
from mutagen.id3 import ID3, ID3NoHeaderError

from music.models import Music
from music.utils import upload_cover_to_ftp


class Command(BaseCommand):
    help = "Restore missing covers from audio_url"

    def handle(self, *args, **kwargs):

        restored = 0
        skipped = 0

        musics = Music.objects.select_related("album").filter(
            cover_url__isnull=True
        )

        for music in musics:

            if not music.audio_url:
                skipped += 1
                continue

            try:

                print(f"Restore -> {music.id} | {music.title}")

                response = requests.get(
                    music.audio_url,
                    timeout=60,
                    stream=True
                )

                if response.status_code != 200:
                    print("Audio not found")
                    continue

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
                    for chunk in response.iter_content(8192):
                        temp_mp3.write(chunk)

                    temp_mp3_path = temp_mp3.name

                try:

                    try:
                        audio = ID3(temp_mp3_path)
                    except ID3NoHeaderError:
                        print("No ID3 tag")
                        continue

                    cover_data = None

                    for key in audio.keys():
                        if key.startswith("APIC"):
                            cover_data = audio[key].data
                            break

                    if not cover_data:
                        print("No cover inside mp3")
                        continue

                    filename = os.path.basename(
                        music.audio_url
                    ).replace(".mp3", ".jpg")

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_cover:
                        temp_cover.write(cover_data)
                        temp_cover_path = temp_cover.name

                    final_cover = os.path.join(
                        os.path.dirname(temp_cover_path),
                        filename
                    )

                    os.rename(temp_cover_path, final_cover)

                    cover_url = upload_cover_to_ftp(final_cover)

                    music.cover_url = cover_url
                    music.save(update_fields=["cover_url"])

                    if music.album and not music.album.cover_url:
                        music.album.cover_url = cover_url
                        music.album.save(update_fields=["cover_url"])

                    os.remove(final_cover)

                    restored += 1

                    print(f"✔ Restored -> {music.title}")

                finally:

                    if os.path.exists(temp_mp3_path):
                        os.remove(temp_mp3_path)

            except Exception as e:
                print(e)

        print("=" * 60)
        print(f"Restored : {restored}")
        print(f"Skipped  : {skipped}")