import threading
import time
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.management import call_command
from .models import Music, Album
from .ftp import delete_file_from_ftp


@receiver(post_delete, sender=Music)
def delete_music_files(sender, instance, **kwargs):
    if instance.audio_url:
        delete_file_from_ftp(instance.audio_url)
    if instance.cover_url:
        delete_file_from_ftp(instance.cover_url)
    if instance.file:
        instance.file.delete(save=False)
    if instance.cover:
        instance.cover.delete(save=False)


def delayed_restore_covers(album_title):
    """تابع کمکی برای ایجاد تاخیر ۲ دقیقه ای در پس زمینه"""
    try:
        print(f"⏳ آلبوم '{album_title}' حذف شد. در انتظار ۲ دقیقه برای بازسازی کاورها...")
        time.sleep(120)  # ۱۲۰ ثانیه = ۲ دقیقه
        call_command('restore_liara_covers')
        print("✅ بازسازی خودکار کاورها پس از تاخیر ۲ دقیقه‌ای انجام شد.")
    except Exception as e:
        print(f"❌ خطا در اجرای با تاخیر دستور بازیابی کاور: {e}")


@receiver(post_delete, sender=Album)
def delete_album_files(sender, instance, **kwargs):
    """
    هنگام حذف آلبوم، یک ترد (Thread) مستقل ایجاد می شود
    تا پس از ۲ دقیقه دستور ریستور را اجرا کند.
    """
    thread = threading.Thread(target=delayed_restore_covers, args=(instance.title,))
    thread.daemon = True
    thread.start()