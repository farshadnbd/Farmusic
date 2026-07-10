import os
import ftplib
import ssl
from django.conf import settings


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found at: {local_file_path}")
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        print(f"⚡ Connecting to FTP for Music ID {instance_id}...")

        # ۱. تلاش برای اتصال با FTP_TLS استاندارد پایتون بدون پچ‌های دستی مخرب
        ftp = ftplib.FTP_TLS()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        try:
            # فعال کردن لایه محافظتی دیتا به روش رسمی پایتون
            ftp.prot_p()
        except Exception as tls_err:
            print(f"⚠️ Secure data channel not supported or rejected: {tls_err}. Trying plain text...")
            # اگر هاست در لایه پروتکل امن به مشکل خورد، سوییچ روی حالت ساده
            ftp.prot_c()

        # ۲. مدیریت پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۳. آپلود فایل
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        print(f"✅ Successfully uploaded to FTP.")

        # ۴. تولید URL مستقیم آهنگ روی هاست دانلود شما
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۵. به‌روزرسانی آدرس در دیتابیس
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۶. پاکسازی فایل موقت از روی دیسک لیارا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False