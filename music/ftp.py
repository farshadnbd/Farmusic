from ftplib import FTP
from urllib.parse import urlparse
from django.conf import settings


def delete_file_from_ftp(url):
    if not url:
        return

    try:
        parsed = urlparse(url)
        remote_path = parsed.path.lstrip("/")
        ftp = FTP()
        ftp.connect(settings.FTP_HOST, 21)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        ftp.cwd("public_html")
        ftp.delete(remote_path)
        ftp.quit()

        print("Deleted:", remote_path)

    except Exception as e:
        print("FTP Delete Error:", e)