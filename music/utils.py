import os
import ftplib
from django.conf import settings


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="tracks"):
    if not os.path.exists(local_file_path):
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        # 🟢 تغییر به FTP_TLS برای پشتیبانی از امنیت پارس‌پک
        ftp = ftplib.FTP_TLS()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        ftp.prot_p() # 🟢 حتماً این خط را اضافه کنید تا کانال دیتای فایل هم امن شود

        # ۲. مدیریت پوشه مقصد
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)

        # ۳. آپلود باکتریایی فایل
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        ftp.quit()

        # ۴. تولید URL نهایی
        download_url = f"https://{settings.FTP_HOST}/{remote_dir}/{file_name}"

        # ۵. به‌روزرسانی امن دیتابیس با متد update (بدون صدا زدن مجدد save)
        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        # ۶. حذف فایل محلی فقط و فقط پس از موفقیت کامل مراحل بالا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

        return True

    except Exception as e:
        # در صورت بروز هرگونه خطای شبکه یا FTP، فایل محلی حذف نمی‌شود تا اطلاعات موزیک گم نشود
        print(f"FTP background upload failed for Music ID {instance_id}: {e}")
        return False