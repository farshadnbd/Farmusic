from django.core.management.base import BaseCommand
from music.models import Music, Album
from music.utils import (upload_to_ftp_and_clean,upload_cover_to_ftp,remote_file_exists,)
import os


class Command(BaseCommand):
    help = "Sync local media with download server"

    def handle(self, *args, **kwargs):

        uploaded_music = 0
        uploaded_cover = 0
        deleted_local = 0
        skipped = 0
        errors = 0

        self.stdout.write(self.style.WARNING("Checking musics..."))

        for music in Music.objects.all():

            try:

                # ================= AUDIO =================

                if music.file:
                    local_audio = music.file.path

                    if os.path.exists(local_audio):
                        # اگر فایل روی هاست وجود ندارد، دوباره آپلود کن
                        if not remote_file_exists(music.audio_url):

                            self.stdout.write(
                                f"Uploading audio -> {music.title}")

                            if upload_to_ftp_and_clean(music.id,local_audio,):
                                uploaded_music += 1
                            else:
                                errors += 1
                                continue

                        # اگر روی هاست وجود دارد، فایل محلی را حذف کن
                        if remote_file_exists(music.audio_url):

                            if os.path.exists(local_audio):
                                os.remove(local_audio)
                                deleted_local += 1

                            music.file.delete(save=False)

                # ================= COVER =================

                if music.cover:
                    local_cover = music.cover.path

                    if os.path.exists(local_cover):
                        if not remote_file_exists(music.cover_url):
                            self.stdout.write(f"Uploading cover -> {music.title}")
                            cover_url = upload_cover_to_ftp(local_cover)

                            if cover_url:
                                music.cover_url = cover_url
                                music.save(update_fields=["cover_url"])
                                uploaded_cover += 1

                            else:
                                errors += 1
                                continue

                        if remote_file_exists(music.cover_url):

                            if os.path.exists(local_cover):
                                os.remove(local_cover)
                                deleted_local += 1

                            music.cover.delete(save=False)
                skipped += 1
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(str(e)))

        self.stdout.write(self.style.WARNING("Checking albums..."))

        for album in Album.objects.all():
            try:
                if album.cover:
                    local_cover = album.cover.path
                    if os.path.exists(local_cover):
                        if not remote_file_exists(album.cover_url):
                            self.stdout.write(f"Uploading album cover -> {album.title}")
                            cover_url = upload_cover_to_ftp(local_cover)

                            if cover_url:
                                album.cover_url = cover_url
                                album.save(update_fields=["cover_url"])

                        if remote_file_exists(album.cover_url):
                            if os.path.exists(local_cover):
                                os.remove(local_cover)
                                deleted_local += 1

                            album.cover.delete(save=False)
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(str(e)))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Finished"))
        self.stdout.write(f"Uploaded audios : {uploaded_music}")
        self.stdout.write(f"Uploaded covers : {uploaded_cover}")
        self.stdout.write(f"Deleted locals  : {deleted_local}")
        self.stdout.write(f"Checked         : {skipped}")
        self.stdout.write(f"Errors          : {errors}")