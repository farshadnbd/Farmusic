import threading
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Music , Album
from .utils import upload_to_ftp_and_clean
from django.db.models.signals import post_delete
from .ftp import delete_file_from_ftp

@receiver(post_save, sender=Music)
def trigger_ftp_upload(sender, instance, created, **kwargs):
    # چک کردن هماهنگ با نام فیلد جدید دیتابیس (instance.file)
    if instance.file and not instance.audio_url:
        local_path = instance.file.path

        # اجرای جاب پس‌زمینه سبک با Threading بدون قفل کردن فرانت‌اند
        def run_in_background():
            success = upload_to_ftp_and_clean(instance.id, local_path)

            # 🌟 بعد از اینکه فایل با موفقیت به هاست دانلود منتقل شد، حالا نسخه به روز شده را برای تلگرام بفرست
            if success:
                # تازه کردن آبجکت از دیتابیس برای گرفتن آدرس جدید audio_url
                updated_instance = Music.objects.get(id=instance.id)
                from music.telegram import send_new_music_to_telegram
                try:
                    send_new_music_to_telegram(updated_instance)
                except Exception as telegram_error:
                    print(f"Telegram automation failed: {telegram_error}")

        # اجرا بلافاصله بعد از نهایی شدن تراکنش پستگرس
        transaction.on_commit(lambda: threading.Thread(target=run_in_background).start())

@receiver(post_delete, sender=Music)
def delete_music_files(sender, instance, **kwargs):

    delete_file_from_ftp(instance.audio_url)
    delete_file_from_ftp(instance.cover_url)

    if instance.file:
        instance.file.delete(save=False)

    if instance.cover:
        instance.cover.delete(save=False)


@receiver(post_delete, sender=Album)
def delete_album_files(sender, instance, **kwargs):

    delete_file_from_ftp(instance.cover_url)
    delete_file_from_ftp(instance.zip_url)

    if instance.cover:
        instance.cover.delete(save=False)

    if instance.zip_file:
        instance.zip_file.delete(save=False)