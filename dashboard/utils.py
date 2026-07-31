from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from django.core.files.base import ContentFile
import os
import tempfile
from django.core.files import File
import requests


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


def normalize_genre(genre_name):
    invalid_genres = {"", "unknown", "none", "null", "n/a", "undefined"}

    if not genre_name:
        return "Unknown"

    genre_name = genre_name.strip()

    if genre_name.lower() in invalid_genres:
        return "Unknown"

    g = (genre_name.lower().replace("_", " ").replace("-", " ").replace("/", " ").replace("&", " ").replace(",", " "))

    # Hip Hop / Rap
    if any(x in g for x in ["rap", "hip hop", "hiphop", "trap"]):
        return "Hip-Hop"

    # Pop
    if "pop" in g:
        return "Pop"

    # Rock
    if any(x in g for x in ["rock", "hard rock", "soft rock", "alternative rock"]):
        return "Rock"

    # Metal
    if "metal" in g:
        return "Metal"

    # Electronic
    if any(x in g for x in ["edm", "electronic", "electro"]):
        return "Electronic"

    # House
    if "house" in g:
        return "House"

    # Techno
    if "techno" in g:
        return "Techno"

    # Trance
    if "trance" in g:
        return "Trance"

    # Dance
    if "dance" in g:
        return "Dance"

    # Dubstep
    if "dubstep" in g:
        return "Dubstep"

    # Jazz
    if "jazz" in g:
        return "Jazz"

    # Blues
    if "blues" in g:
        return "Blues"

    # Country
    if "country" in g:
        return "Country"

    # Folk
    if "folk" in g:
        return "Folk"

    # Classical
    if any(x in g for x in ["classical", "orchestra", "orchestral", "instrumental"]):
        return "Classical"

    # Soundtrack
    if any(x in g for x in ["soundtrack", "ost", "score"]):
        return "Soundtrack"

    # Lo-Fi
    if any(x in g for x in ["lofi", "lo fi", "lo-fi"]):
        return "Lo_Fi"

    # Ambient
    if "ambient" in g:
        return "Ambient"

    # Reggae
    if "reggae" in g:
        return "Reggae"

    # Latin
    if any(x in g for x in ["latin", "latino"]):
        return "Latin"

    # R&B
    if any(x in g for x in ["r&b", "rnb"]):
        return "R&B"

    return genre_name.title()
