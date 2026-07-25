import os
import ftplib
from django.conf import settings


def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="public_html/tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found at: {local_file_path}")
        return False

    from music.models import Music
    file_name = os.path.basename(local_file_path)

    try:
        print(f"⚡ Connecting via Plain FTP for Music ID {instance_id}...")

        ftp = ftplib.FTP()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        # ۲. مدیریت و ورود گام‌به‌گام به پوشه مقصد
        path_parts = remote_dir.split('/')
        for part in path_parts:
            if part:
                try:
                    ftp.cwd(part)  # وارد پوشه این مرحله می‌شود (مثلاً ابتدا public_html و سپس tracks)
                except Exception:
                    try:
                        ftp.mkd(part)  # اگر وجود نداشت، پوشه را می‌سازد
                        ftp.cwd(part)  # سپس وارد آن می‌شود
                    except Exception as e:
                        print(f"⚠️ Could not create or enter directory '{part}': {e}")

        # ۳. آپلود فایل صوتی
        print(f"📤 Uploading {file_name} to host...")
        with open(local_file_path, 'rb') as file_to_upload:
            ftp.storbinary(f"STOR {file_name}", file_to_upload)

        try:
            ftp.quit()
        except Exception:
            ftp.close()

        print(f"✅ Successfully uploaded to Plain FTP.")

        # ۴. تولید URL مستقیم آهنگ با پروتکل http (چون هاست دانلود SSL ندارد)
        # همچنین بخش public_html را از URL حذف می‌کنیم چون این پوشه روت اینترنتی شماست
        url_dir = remote_dir.replace("public_html/", "").replace("public_html", "")
        if url_dir and not url_dir.startswith("/"):
            url_dir = f"/{url_dir}"

        # اصلاح اصلی: استفاده از DOWNLOAD_BASE_URL به جای FTP_HOST
        download_url = f"http://{settings.DOWNLOAD_BASE_URL}{url_dir}/{file_name}"

        # ۵. به‌روزرسانی آدرس صوتی در دیتابیس
        Music.objects.filter(id=instance_id).update(audio_url=download_url)
        music = Music.objects.select_related("album").get(id=instance_id)

        # ۶. پاکسازی فایل موقت از روی دیسک اصلی لیارا
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"🗑️ Cleaned up local file from Liara disk.")

        return True

    except Exception as e:
        print(f"❌ FTP background upload failed for Music ID {instance_id}: {e}")
        return False


def upload_file_to_ftp(local_file_path, remote_dir):
    if not os.path.exists(local_file_path):
        return None

    file_name = os.path.basename(local_file_path)

    ftp = ftplib.FTP()
    ftp.connect(settings.FTP_HOST, 21, timeout=30)
    ftp.login(settings.FTP_USER, settings.FTP_PASS)

    path_parts = remote_dir.split("/")

    for part in path_parts:
        if part:
            try:
                ftp.cwd(part)
            except Exception:
                try:
                    ftp.mkd(part)
                    ftp.cwd(part)
                except:
                    pass

    with open(local_file_path, "rb") as f:
        ftp.storbinary(f"STOR {file_name}", f)

    try:
        ftp.quit()
    except:
        ftp.close()

    url_dir = remote_dir.replace("public_html/", "").replace("public_html", "")
    if url_dir and not url_dir.startswith("/"):
        url_dir = "/" + url_dir

    return f"http://{settings.DOWNLOAD_BASE_URL}{url_dir}/{file_name}"


def upload_cover_to_ftp(local_file_path):
    return upload_file_to_ftp(local_file_path, "public_html/covers")
