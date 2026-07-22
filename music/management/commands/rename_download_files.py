import os
import re
from pathlib import Path
from ftplib import FTP
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from music.models import Music, Album


FTP_HOST = "3264450084.cloudydl.com"
FTP_PORT = 21
FTP_USER = "pz24788"
FTP_PASSWORD = "@Farshad1380"

BASE_URL = "https://dl.farmusic.ir"


def safe_filename(filename):
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()

    # حذف کاراکترهای غیرمجاز
    stem = re.sub(r'[<>:"/\\|?*]', "", stem)

    # اگر " - " وجود داشت به یک خط تیره تبدیل شود
    stem = stem.replace(" - ", "-")

    # بقیه فاصله‌ها هم خط تیره شوند
    stem = re.sub(r"\s+", "-", stem)

    # فقط حروف انگلیسی، فارسی، عدد و خط تیره بماند
    stem = re.sub(r"[^A-Za-z0-9\u0600-\u06FF_-]", "", stem)

    # خط تیره‌های پشت سرهم
    stem = re.sub(r"-{2,}", "-", stem)

    # حذف خط تیره ابتدا و انتها
    stem = stem.strip("-")

    return f"{stem}{ext}"


class Command(BaseCommand):
    help = "Rename files on download host and update database."

    def handle(self, *args, **kwargs):

        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASSWORD)

        self.stdout.write(self.style.SUCCESS("Connected to FTP"))

        # ---------------- Tracks ----------------

        ftp.cwd("public_html/tracks")

        rename_map = {}

        for old_name in ftp.nlst():

            new_name = safe_filename(old_name)

            if old_name != new_name:
                try:
                    ftp.rename(old_name, new_name)
                    self.stdout.write(f"{old_name} -> {new_name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    continue

            rename_map[old_name] = new_name

        for music in Music.objects.exclude(audio_url=""):

            old_name = os.path.basename(
                urlparse(music.audio_url).path
            )

            if old_name in rename_map:

                music.audio_url = (
                    f"{BASE_URL}/tracks/{rename_map[old_name]}"
                )

                music.save(update_fields=["audio_url"])

        # ---------------- Covers ----------------

        ftp.cwd("../covers")

        rename_map = {}

        for old_name in ftp.nlst():

            new_name = safe_filename(old_name)

            if old_name != new_name:
                try:
                    ftp.rename(old_name, new_name)
                    self.stdout.write(f"{old_name} -> {new_name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    continue

            rename_map[old_name] = new_name

        for music in Music.objects.exclude(cover_url__isnull=True).exclude(cover_url=""):

            old_name = os.path.basename(
                urlparse(music.cover_url).path
            )

            if old_name in rename_map:

                music.cover_url = (
                    f"{BASE_URL}/covers/{rename_map[old_name]}"
                )

                music.save(update_fields=["cover_url"])

        for album in Album.objects.exclude(cover_url__isnull=True).exclude(cover_url=""):

            old_name = os.path.basename(
                urlparse(album.cover_url).path
            )

            if old_name in rename_map:

                album.cover_url = (
                    f"{BASE_URL}/covers/{rename_map[old_name]}"
                )

                album.save(update_fields=["cover_url"])

        ftp.quit()

        self.stdout.write(self.style.SUCCESS("Done."))