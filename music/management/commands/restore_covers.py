import os
import tempfile
import requests

from django.core.management.base import BaseCommand
from mutagen.id3 import ID3

from music.models import Music
from music.utils import upload_cover_to_ftp


class Command(BaseCommand):
    help = "Restore covers from audio_url"

    def handle(self, *args, **kwargs):

        restored = 0

        for music in Music.objects.select_related("album"):

            if not music.audio_url:
                continue

            try:
                print(f"Checking {music.id} - {music.title}")

                response = requests.get(music.audio_url, timeout=60)

                if response.status_code != 200:
                    print("Audio not found")
                    continue

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:
                    temp_mp3.write(response.content)
                    temp_mp3_path = temp_mp3.name

                try:
                    audio = ID3(temp_mp3_path)

                    cover_data = None

                    for key in audio.keys():
                        if key.startswith("APIC"):
                            cover_data = audio[key].data
                            break

                    if not cover_data:
                        print("No cover inside mp3")
                        continue

                    filename = os.path.basename(music.audio_url).replace(".mp3", ".jpg")

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_cover:
                        temp_cover.write(cover_data)
                        temp_cover_path = temp_cover.name

                    # اسم فایل را مثل قبل قرار می‌دهیم
                    new_path = os.path.join(
                        os.path.dirname(temp_cover_path),
                        filename
                    )

                    os.rename(temp_cover_path, new_path)

                    cover_url = upload_cover_to_ftp(new_path)

                    music.cover_url = cover_url
                    music.save(update_fields=["cover_url"])

                    if music.album and not music.album.cover_url:
                        music.album.cover_url = cover_url
                        music.album.save(update_fields=["cover_url"])

                    os.remove(new_path)

                    restored += 1

                    print(f"Restored -> {music.title}")

                finally:
                    if os.path.exists(temp_mp3_path):
                        os.remove(temp_mp3_path)

            except Exception as e:
                print(e)

        print("=" * 60)
        print(f"Restored {restored} covers")