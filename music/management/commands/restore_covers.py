import os
import tempfile
import requests

from django.core.management.base import BaseCommand
from mutagen.id3 import ID3, ID3NoHeaderError
from PIL import Image, ImageOps

from music.models import Music
from music.utils import upload_cover_to_ftp


class Command(BaseCommand):
    help = "Restore missing FTP covers from MP3"

    def handle(self, *args, **kwargs):
        restored = 0
        skipped = 0
        failed = 0
        musics = Music.objects.select_related("album").all()
        self.stdout.write(f"Checking {musics.count()} musics...")

        for music in musics:

            if not music.audio_url:
                skipped += 1
                continue
            # -----------------------------
            # بررسی وجود فایل کاور روی FTP
            # -----------------------------
            needs_restore = False

            if not music.cover_url:
                needs_restore = True
            else:
                try:
                    head = requests.head(music.cover_url,timeout=10,allow_redirects=True,)

                    if head.status_code != 200:
                        needs_restore = True

                except Exception:
                    needs_restore = True

            if not needs_restore:
                skipped += 1
                continue

            temp_mp3_path = None
            cover_path = None

            try:
                print(f"\nRestore -> {music.id} | {music.title}")
                response = requests.get(music.audio_url,timeout=60,)

                if response.status_code != 200:
                    print("Audio not found")
                    failed += 1
                    continue

                with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3",) as temp_mp3:
                    temp_mp3.write(response.content)
                    temp_mp3_path = temp_mp3.name
                try:
                    try:
                        audio = ID3(temp_mp3_path)
                    except ID3NoHeaderError:
                        print("No ID3 tag")
                        failed += 1
                        continue

                    cover_data = None

                    for key in audio.keys():
                        if key.startswith("APIC"):
                            cover_data = audio[key].data
                            break

                    if not cover_data:
                        print("No APIC cover")
                        failed += 1
                        continue

                    filename = os.path.basename(
                        music.audio_url
                    ).replace(".mp3", ".jpg")

                    with tempfile.NamedTemporaryFile(delete=False,suffix=".jpg",) as temp_cover:
                        temp_cover.write(cover_data)
                        cover_path = temp_cover.name

                    final_cover = os.path.join(os.path.dirname(cover_path),filename,)
                    os.rename(cover_path, final_cover)
                    cover_path = final_cover

                    # --------------------------
                    # Crop + Compress
                    # --------------------------
                    image = Image.open(cover_path).convert("RGB")
                    image = ImageOps.fit(image,(400, 400),Image.Resampling.LANCZOS,)
                    image.save(cover_path,"JPEG",quality=85,optimize=True,)
                    # --------------------------
                    # Upload
                    # --------------------------
                    cover_url = upload_cover_to_ftp(cover_path)
                    music.cover_url = cover_url
                    music.save(update_fields=["cover_url"])

                    if music.album:
                        if not music.album.cover_url:
                            music.album.cover_url = cover_url
                            music.album.save(update_fields=["cover_url"])

                    restored += 1
                    print(f"✔ Restored -> {music.title}")

                finally:
                    if temp_mp3_path and os.path.exists(temp_mp3_path):
                        os.remove(temp_mp3_path)

                    if cover_path and os.path.exists(cover_path):
                        os.remove(cover_path)

            except Exception as e:
                failed += 1
                print(f"ERROR {music.id}: {e}")

        print("=" * 60)
        print(f"Restored : {restored}")
        print(f"Skipped  : {skipped}")
        print(f"Failed   : {failed}")