import os
import re
from ftplib import FTP
from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from music.models import Music, Album
from django.conf import settings


FTP_HOST = "3264450084.cloudydl.com"
FTP_PORT = 21
FTP_USER = "pz24788"
FTP_PASSWORD = "@Farshad1380"

BASE_URL = "https://dl.farmusic.ir"


def safe_filename(filename):
    name, ext = os.path.splitext(filename)

    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)

    return name.strip("_") + ext.lower()


class Command(BaseCommand):
    help = "Rename files on download host and update database."

    def handle(self, *args, **kwargs):

        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASSWORD)

        self.stdout.write("Connected.")

        # ---------- Tracks ----------

        ftp.cwd("public_html/tracks")

        files = ftp.nlst()

        rename_map = {}

        for old in files:

            new = safe_filename(old)

            if old != new:

                try:
                    ftp.rename(old, new)
                    self.stdout.write(f"{old} -> {new}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    continue

            rename_map[old] = new

        for music in Music.objects.all():

            if music.audio_url:

                old_name = os.path.basename(
                    urlparse(music.audio_url).path
                )

                if old_name in rename_map:

                    music.audio_url = (
                        f"{BASE_URL}/tracks/{rename_map[old_name]}"
                    )

                    music.save(update_fields=["audio_url"])

        # ---------- Covers ----------

        ftp.cwd("../covers")

        files = ftp.nlst()

        rename_map = {}

        for old in files:

            new = safe_filename(old)

            if old != new:

                try:
                    ftp.rename(old, new)
                    self.stdout.write(f"{old} -> {new}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    continue

            rename_map[old] = new

        for music in Music.objects.all():

            if music.cover_url:

                old_name = os.path.basename(
                    urlparse(music.cover_url).path
                )

                if old_name in rename_map:

                    music.cover_url = (
                        f"{BASE_URL}/covers/{rename_map[old_name]}"
                    )

                    music.save(update_fields=["cover_url"])

        for album in Album.objects.all():

            if getattr(album, "cover_url", None):

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