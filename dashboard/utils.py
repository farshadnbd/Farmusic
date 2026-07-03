from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from django.core.files.base import ContentFile
import os
import zipfile
import tempfile
from django.core.files import File


def extract_metadata(mp3_file):
    try:
        # حتماً نشانگر فایل به ابتدای فایل هدایت شود
        mp3_file.seek(0)
        audio = EasyID3(mp3_file)

        return {
            "title": audio.get("title", [None])[0],
            "artist": audio.get("artist", [None])[0],
            "album": audio.get("album", [None])[0],
            "genre": audio.get("genre", [None])[0],
            "tracknumber": audio.get("tracknumber", [None])[0],
            "date": audio.get("date", [None])[0],
        }
    except Exception:
        return {}


def extract_cover(mp3_file):
    try:
        # ریست کردن مجدد نشانگر فایل برای متد دوم
        mp3_file.seek(0)
        audio = ID3(mp3_file)

        # پیدا کردن تگ کاور (APIC)
        for key in audio.keys():
            if key.startswith("APIC"):
                tag = audio[key]
                # ساخت یک فایل معتبر برای جنگو
                return ContentFile(tag.data, name=f"cover_{mp3_file.name.replace('.mp3', '')}.jpg")
    except Exception:
        pass
    return None


def extract_lyrics(mp3_file):
    try:
        # ریست کردن مجدد نشانگر فایل
        mp3_file.seek(0)
        audio = ID3(mp3_file)

        # پیدا کردن تگ متن آهنگ (USLT)
        for key in audio.keys():
            if key.startswith("USLT"):
                tag = audio[key]

                # اگر متد تکست وجود داشت
                if tag.text:
                    # ۱. ابتدا کل متن را به صورت کامل استخراج می‌کنیم
                    if isinstance(tag.text, list):
                        full_text = "\n".join(str(t) for t in tag.text)
                    else:
                        full_text = str(tag.text)

                    # ۲. فاصله‌های خالی ابتدا و انتها را پاک می‌کنیم تا شمارش دقیق باشد
                    full_text = full_text.strip()

                    # ۳. شرط جدید: اگر طول متن کمتر از ۱۵ حرف بود، انگار لیریکس ندارد
                    if len(full_text) < 25:
                        return None

                    # اگر بیشتر از ۱۵ حرف بود، کل متن را برمی‌گرداند
                    return full_text

    except Exception:
        pass
    return None


def generate_album_zip(album):
    musics = album.music_set.all()

    # اگر آلبوم هیچ آهنگی نداشت
    if not musics.exists():
        return None

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.close()

    try:
        with zipfile.ZipFile(temp_file.name, "w", zipfile.ZIP_DEFLATED) as zipf:
            added_count = 0

            for music in musics:
                if music.file and hasattr(music.file, "path") and os.path.exists(music.file.path):
                    zipf.write(
                        music.file.path,
                        arcname=os.path.basename(music.file.name)
                    )
                    added_count += 1

        # اگر هیچ فایل آهنگی داخل zip نرفت
        if added_count == 0:
            try:
                os.remove(temp_file.name)
            except:
                pass
            return None

        with open(temp_file.name, "rb") as f:
            safe_title = album.title.replace("/", "-").replace("\\", "-")
            album.zip_file.save(
                f"{safe_title}.zip",
                File(f),
                save=True
            )

        return album.zip_file

    finally:
        try:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
        except:
            pass