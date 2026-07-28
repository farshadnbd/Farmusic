import os
import ftplib
from django.conf import settings
from music.models import Music

def upload_to_ftp_and_clean(instance_id, local_file_path, remote_dir="public_html/tracks"):
    if not os.path.exists(local_file_path):
        print(f"❌ File not found: {local_file_path}")
        return False

    filename = os.path.basename(local_file_path)
    ftp = None

    try:
        print(f"⚡ Connecting FTP...")
        ftp = ftplib.FTP()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)

        for part in remote_dir.split("/"):
            if not part:
                continue

            try:
                ftp.cwd(part)

            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)

        print(f"📤 Uploading {filename}")
        ftp.sendcmd("TYPE I")

        with open(local_file_path, "rb") as f:
            ftp.storbinary(f"STOR {filename}", f)
            print("PWD AFTER MP3 =", ftp.pwd())

        remote = (remote_dir.replace("public_html/", "").replace("public_html", "").strip("/"))
        download_url = f"https://{settings.DOWNLOAD_BASE_URL}"
        print("DOWNLOAD URL =", download_url)

        if remote:
            download_url += f"/{remote}"

        download_url += f"/{filename}"

        Music.objects.filter(id=instance_id).update(audio_url=download_url)

        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print("🗑 Local mp3 removed.")

        print("✅ Upload success")

        return True

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                try:
                    ftp.close()
                except:
                    pass


def upload_file_to_ftp(local_file_path, remote_dir):
    if not os.path.exists(local_file_path):
        print("❌ Cover not found.")
        return None

    filename = os.path.basename(local_file_path)
    ftp = None

    try:
        ftp = ftplib.FTP()
        ftp.connect(settings.FTP_HOST, 21, timeout=30)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        print("PWD =", ftp.pwd())
        print("LIST =", ftp.nlst())

        for part in remote_dir.split("/"):
            if not part:
                continue

            try:
                ftp.cwd(part)

            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)

        with open(local_file_path, "rb") as f:
            ftp.storbinary(f"STOR {filename}", f)

        print("PWD AFTER =", ftp.pwd())

        remote = (remote_dir.replace("public_html/", "").replace("public_html", "").strip("/"))

        url = f"https://{settings.DOWNLOAD_BASE_URL}"

        if remote:
            url += f"/{remote}"

        url += f"/{filename}"

        return url

    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                try:
                    ftp.close()
                except:
                    pass


def upload_cover_to_ftp(local_file_path):
    return upload_file_to_ftp(local_file_path, "public_html/covers", )
