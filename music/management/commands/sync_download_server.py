from django.core.management.base import BaseCommand
from music.models import Music
from music.utils import upload_to_ftp_and_clean, remote_file_exists
import os


class Command(BaseCommand):
    help = "Sync audio files with download server only"

    def handle(self, *args, **kwargs):
        uploaded = 0
        deleted_local = 0
        skipped = 0
        errors = 0

        self.stdout.write(self.style.WARNING(
            "Checking audio files only..."
        ))

        for music in Music.objects.exclude(file="").iterator(chunk_size=200):
            try:
                if not music.file:
                    skipped += 1
                    continue

                local_audio = music.file.path
                audio_url = music.audio_url

                if not os.path.isfile(local_audio):
                    self.stdout.write(
                        f"Local file missing: {music.title}"
                    )
                    skipped += 1
                    continue

                if not audio_url:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Audio URL missing: {music.title}"
                        )
                    )
                    errors += 1
                    continue

                # فقط یک بار بررسی می‌کنیم فایل روی هاست وجود دارد یا نه
                if remote_file_exists(audio_url):
                    # فایل روی هاست وجود دارد؛ نسخه محلی را حذف می‌کنیم
                    os.remove(local_audio)
                    music.file = ""
                    music.save(update_fields=["file"])

                    deleted_local += 1
                    continue

                self.stdout.write(f"Uploading audio: {music.title}")

                # این تابع طبق پیاده‌سازی فعلی پروژه فراخوانی می‌شود.
                # قبل از حذف فایل، موفقیت آپلود باید تأیید شده باشد.
                if upload_to_ftp_and_clean(music.id, local_audio):
                    # اگر تابع فایل محلی را خودش حذف نکرده باشد
                    if os.path.isfile(local_audio):
                        os.remove(local_audio)

                    music.file = ""
                    music.save(update_fields=["file"])

                    uploaded += 1
                else:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Upload failed: {music.title}"
                        )
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"{music.title}: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Finished"))
        self.stdout.write(f"Uploaded audios : {uploaded}")
        self.stdout.write(f"Deleted locals  : {deleted_local}")
        self.stdout.write(f"Skipped         : {skipped}")
        self.stdout.write(f"Errors          : {errors}")