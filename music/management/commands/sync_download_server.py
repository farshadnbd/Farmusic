
from django.core.management.base import BaseCommand
from music.models import Music
from music.utils import upload_to_ftp_and_clean
import os


class Command(BaseCommand):
    help = "Upload local audio files to the download server only"

    def handle(self, *args, **kwargs):
        uploaded = 0
        skipped = 0
        errors = 0

        self.stdout.write("Uploading local audio files only...")

        queryset = Music.objects.exclude(file="").order_by("id")

        for music in queryset.iterator(chunk_size=200):
            try:
                if not music.file:
                    skipped += 1
                    continue

                local_audio = music.file.path

                if not os.path.isfile(local_audio):
                    skipped += 1
                    continue

                if not os.path.getsize(local_audio):
                    self.stdout.write(
                        self.style.ERROR(
                            f"Empty local file: {music.title}"
                        )
                    )
                    errors += 1
                    continue

                self.stdout.write(f"Uploading: {music.title}")

                # This helper currently deletes the local file
                # after FTP upload and updates audio_url.
                success = upload_to_ftp_and_clean(
                    music.id,
                    local_audio,
                )

                if success:
                    # Confirm the helper has cleared the model field.
                    music.refresh_from_db()

                    if not music.audio_url:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Upload URL missing after upload: "
                                f"{music.title}"
                            )
                        )
                        errors += 1
                        continue

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
                    self.style.ERROR(f"{music.title}: {e}")
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Finished"))
        self.stdout.write(f"Uploaded audios: {uploaded}")
        self.stdout.write(f"Skipped: {skipped}")
        self.stdout.write(f"Errors: {errors}")