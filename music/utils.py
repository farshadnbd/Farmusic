import os
import ftplib
import ssl
from django.conf import settings


# 🌟 کلاس پچ‌شده نهایی و استاندارد برای هاست‌های دانلود ایران (پارس‌پک)
class FixedFTP_TLS(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        """مجبور کردن کانال دیتا به استفاده از نشست کانال اصلی (Session Reuse)"""
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._secure_data_conn:
            # کپی کردن دقیق نشست SSL کانال اصلی روی کانال دیتا برای جلوگیری از خطای پروتکل
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session
            )
        return conn, size


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found at: {local_file_path}")
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        print(f"⚡ Connecting via Fixed FTP_TLS for Music ID {instance_id}...")

        # ۱. اتصال امن با کلاس پچ‌شده جدید
        ftp = FixedFTP_TLS()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        # ۲. فعال‌سازی کانال دیتا به صورت امن
        ftp.prot_p()

        # ۳. مدیریت پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۴. آپلود فایل
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        print(f"✅ Successfully uploaded to FTP.")

        # ۵. تولید URL مستقیم آهنگ
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۶. به‌روزرسانی آدرس در دیتابیس
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۷. پاکسازی فایل موقت از روی دیسک لیارا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False