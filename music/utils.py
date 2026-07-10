import os
import ftplib
import ssl
from django.conf import settings


# 🌟 کلاس پچ‌شده فوق‌العاده سبک برای حل تداخل امنیتی و SSL با سرور پارس‌پک
class PatchedFTP_TLS(ftplib.FTP_TLS):
    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        """بازنویسی متد آپلود برای بستن امن لایه SSL به منظور جلوگیری از خطای پروتکل"""
        self.voidcmd('TYPE I')
        with self.transfercmd(cmd, rest) as conn:
            while True:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)

            # 🔐 شگرد اصلی: باز کردن (unwrap) امن لایه SSL قبل از بستن نهایی کانال
            if isinstance(conn, ssl.SSLSocket):
                try:
                    conn.unwrap()
                except Exception:
                    pass
        return self.voidresp()


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found at: {local_file_path}")
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        print(f"⚡ Connecting via Secure FTP for Music ID {instance_id}...")

        # ۱. برقراری اتصال امن با استفاده از کلاس اصلاح‌شده
        ftp = PatchedFTP_TLS()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        ftp.prot_p()  # امن‌سازی کانال دیتا

        # ۲. مدیریت و ورود به پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۳. آپلود باکتریایی فایل صوتی بدون کرش کردن پروتکل
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        print(f"✅ Successfully uploaded to FTP.")

        # ۴. تولید لینک مستقیم آهنگ روی هاست دانلود شما
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۵. به‌روزرسانی آدرس صوتی در دیتابیس (بدون لوپ سیگنال)
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۶. پاکسازی فایل موقت از روی دیسک لیارا برای صفر ماندن فضا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False