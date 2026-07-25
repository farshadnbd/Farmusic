import os
import tempfile
import requests

from django.core.management.base import BaseCommand
from mutagen.id3 import ID3, ID3NoHeaderError
from PIL import Image, ImageOps

from music.models import Music
from music.utils import upload_cover_to_ftp


class Command(BaseCommand):
    help = "Restore missing covers from audio_url"

    def handle(self, *args, **kwargs):

        restored = 0
        skipped = 0

        # فقط موزیک‌هایی که کاور ندارند
        musics = Music.objects.select_related("album").filter(
            cover_url__isnull=True
        )

        self.stdout.write(
            f"Found {musics.count()} musics without covers"
        )

        for music in musics:

            if not music.audio_url:
                skipped += 1
                continue

            temp_mp3_path = None
            cover_path = None

            try:
                print(f"\nChecking {music.id} - {music.title}")
                response = requests.get(music.audio_url, timeout=60)

                if response.status_code != 200:
                    print("Audio not found")
                    skipped += 1
                    continue

                # ذخیره موقت MP3
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3:

                    temp_mp3.write(response.content)
                    temp_mp3_path = temp_mp3.name

                try:

                    try:
                        audio = ID3(temp_mp3_path)

                    except ID3NoHeaderError:
                        print("No ID3 tag")
                        skipped += 1
                        continue

                    cover_data = None

                    for key in audio.keys():

                        if key.startswith("APIC"):
                            cover_data = audio[key].data
                            break

                    if not cover_data:
                        print("No cover inside mp3")
                        skipped += 1
                        continue

                    filename = os.path.basename(music.audio_url).replace(".mp3", ".jpg")
                    # ساخت فایل کاور موقت
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_cover:

                        temp_cover.write(cover_data)
                        cover_path = temp_cover.name

                    # تغییر نام
                    new_path = os.path.join(os.path.dirname(cover_path), filename)

                    os.rename(cover_path, new_path)

                    cover_path = new_path
                    # ==========================
                    # آماده سازی برای سایت
                    # crop + resize + compress
                    # ===================
                    image = Image.open(cover_path).convert("RGB")
                    image = ImageOps.fit(image, (400, 400), Image.Resampling.LANCZOS)
                    image.save(cover_path, "JPEG", quality=85, optimize=True)
                    print("Cover optimized")
                    # آپلود کاور
                    cover_url = upload_cover_to_ftp(cover_path)
                    music.cover_url = cover_url
                    music.save(update_fields=["cover_url"])

                    # اگر آلبوم کاور ندارد
                    if (
                            music.album
                            and not music.album.cover_url
                    ):
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
                print(f"ERROR {music.id}: {e}")

        print("=" * 60)
        print(f"Restored: {restored}")
        print(f"Skipped : {skipped}")
