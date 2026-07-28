from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Music, Album
from .ftp import delete_file_from_ftp


@receiver(post_delete, sender=Music)
def delete_music_files(sender, instance, **kwargs):
    # حذف فایل صوتی از هاست دانلود
    if instance.audio_url:
        delete_file_from_ftp(instance.audio_url)

    # حذف کاور از هاست دانلود
    if instance.cover_url:
        delete_file_from_ftp(instance.cover_url)

    # حذف فایل‌های محلی (اگر وجود داشته باشند)
    if instance.file:
        instance.file.delete(save=False)

    if instance.cover:
        instance.cover.delete(save=False)


@receiver(post_delete, sender=Album)
def delete_album_files(sender, instance, **kwargs):
    # عمداً خالی است
    # چون کاور آلبوم همان کاور موزیک‌هاست و نباید هنگام حذف آلبوم پاک شود.
    pass