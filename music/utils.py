import os
import ftplib
import ssl
from django.conf import settings


# 🌟 یک کلاس سفارشی برای حل مشکل تداخل SSL/TLS با هاست دانلود پارس‌پک
class PatchedFTP_TLS(ftplib.FTP_TLS):
    def ntrusted_handshake(self):
        """حل مشکل تداخل نشست لایه امنیتی متداول در هاست‌های دانلود ایران"""
        if isinstance(self.sock, ssl.SSLSocket):
            self.sock.unwrap()
        super().voidcmd('PBSZ 0')
        super().voidcmd('PROT P')

    def ntransfercmd(self, cmd, rest=None):
        host, port = self.ntarget_host_port()
        conn = self.ntransferred_connection(host, port)
        if self._secure_data_conn:
            # کپی کردن نشست برای جلوگیری از خطای امنیتی سرور FTP
            conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
        return conn, getattr(conn, 'fileno', lambda: None)()

    # بازنویسی متد داخلی برای برطرف کردن باگ EOF سرور
    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        self.voidcmd('TYPE I')
        with self.transfercmd(cmd, rest) as conn:
            while 1:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # رفع باگ قطع ناگهانی پروتکل SSL
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
        print(f"⚡ Starting secure FTP connection for Music ID {instance_id}...")

        # استفاده از کلاس پچ‌شده به جای کلاس خام پایتون
        ftp = PatchedFTP_TLS()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        # فعال‌سازی کانال دیتا به صورت امن مطابق ساختار هاست شما
        ftp.prot_p()

        # ۲. مدیریت پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۳. آپلود باکتریایی فایل صوتی بدون قطعی پروتکل
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        ftp.quit()
        print(f"✅ Successfully uploaded to FTP.")

        # ۴. تولید URL نهایی هاست دانلود شما
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۵. به‌روزرسانی امن دیتابیس بدون لوپ سیگنال
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۶. پاکسازی فایل از روی دیسک اصلی لیارا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False