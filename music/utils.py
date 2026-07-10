import os
import ftplib
from django.conf import settings


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found at: {local_file_path}")
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        print(f"⚡ Connecting via Plain FTP for Music ID {instance_id}...")

        # 🟢 سوییچ به FTP معمولی و خام بدون لایه دست‌وپاگیر TLS
        ftp = ftplib.FTP()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        # ۲. مدیریت و ورود به پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۳. آپلود باکتریایی فایل صوتی
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        print(f"✅ Successfully uploaded to Plain FTP.")

        # ۴. تولید URL مستقیم آهنگ روی هاست دانلود شما
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۵. به‌روزرسانی آدرس صوتی در دیتابیس (بدون تحریک لوپ سیگنال)
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۶. پاکسازی فایل موقت از روی دیسک اصلی لیارا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False