import os
import re
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse

from music.models import TelegramFile


# 🟢 تمامی امپورت‌های جنگو را از بالای صفحه حذف کردیم


def send_new_music_to_telegram(music):
    """ارسال آهنگ جدید سایت به کانال تلگرام"""
    music_url = f"{settings.SITE_URL}/music/{music.id}/{music.slug_en}/"

    caption = (
        "🎵 <b>آهنگ جدید منتشر شد</b>\n\n"
        f"🎼 {music.title}\n"
        f"🎤 {music.artist.name if music.artist else 'ناشناس'}\n\n"
        f"🔗 <a href='{music_url}'>مشاهده و پخش آهنگ</a>"
    )

    files = None
    photo_file = None

    if music.cover and hasattr(music.cover, 'path'):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        try:
            photo_file = open(music.cover.path, "rb")
            files = {"photo": photo_file}
        except Exception as e:
            print("Cover file open error:", e)
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": caption,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

    try:
        # بدون پروکسی درخواست بفرستید تا سرور آلمان مستقیم وصل شود
        response = requests.post(url, data=data, files=files, timeout=15)
        print("Telegram Send Status:", response.status_code)
    except Exception as e:
        print("Telegram Send Error:", e)
    finally:
        if photo_file:
            photo_file.close()


def process_telegram_audio(audio_data):
    """دریافت فایل صوتی از تلگرام، استخراج اطلاعات و ذخیره در جنگو"""

    # 🔥 دوقلو کردن امپورت‌ها داخل تابع برای جلوگیری از کرش و Circular Import
    from music.models import Music, Album, Artist, Genre, ArtistFollow
    from accounts.models import Notification
    from dashboard.utils import extract_cover, extract_metadata, extract_lyrics

    file_id = audio_data.get('file_id')
    if TelegramFile.objects.filter(file_id=file_id).exists():
        print("⛔ این فایل قبلاً وارد سایت شده است.")
        return True
    file_name = audio_data.get('file_name', 'telegram_audio.mp3')

    if not file_name.endswith('.mp3'):
        file_name += '.mp3'

    try:
        # ۱. گرفتن مسیر فایل از سرور تلگرام
        get_file_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        file_info_res = requests.get(get_file_url, timeout=15).json()

        if not file_info_res.get('ok'):
            print("❌ خطا در دریافت اطلاعات فایل از تلگرام:", file_info_res)
            return False

        file_path = file_info_res['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"

        # ۲. دانلود واقعی فایل صوتی به صورت بایت‌ها
        print(f"📥 در حال دانلود آهنگ از تلگرام: {file_name}")
        file_content = requests.get(download_url, timeout=30).content
        mp3_file = ContentFile(file_content, name=file_name)

        # ۳. استخراج متاداده‌ها
        metadata = extract_metadata(mp3_file)
        raw_artist = metadata.get("artist") or audio_data.get("performer") or "Unknown Artist"
        title = metadata.get("title") or audio_data.get("title") or file_name.replace(".mp3", "")

        # ۴. تفکیک هوشمند خواننده‌ها
        split_pattern = re.compile(r'\s+(?:ft\.?|feat\.?|&|/|and)\s+|[,\u060C]', re.IGNORECASE)
        artist_names = [name.strip() for name in split_pattern.split(raw_artist) if name.strip()]

        if not artist_names:
            artist_names = ["Unknown Artist"]

        main_artist_name = artist_names[0]
        artist, _ = Artist.objects.get_or_create(name=main_artist_name)
        search_aliases_combined = ", ".join(artist_names)

        if len(artist_names) > 1:
            featured_artists_str = ", ".join(artist_names[1:])
            display_title = f"{title} (Ft. {featured_artists_str})"
        else:
            display_title = title

        # ۵. مدیریت ژانر
        genre_name = metadata.get("genre") or "Unknown"
        for separator in ["&", "/", "and"]:
            if separator in genre_name:
                genre_name = genre_name.split(separator)[0]
        genre, _ = Genre.objects.get_or_create(name=genre_name.strip())

        # ۶. مدیریت آلبوم
        album_name = metadata.get("album")
        album = None
        if album_name:
            album, created = Album.objects.get_or_create(title=album_name, artist=artist)

        track_number = None
        if metadata.get("tracknumber"):
            try:
                track_number = int(metadata["tracknumber"].split("/")[0])
            except:
                pass

        year = None
        if metadata.get("date"):
            try:
                year = int(metadata["date"][:4])
            except:
                pass

        lyrics = extract_lyrics(mp3_file)

        # ۷. ذخیره نهایی آهنگ در دیتابیس جنگو
        music = Music.objects.create(
            title=display_title,
            artist=artist,
            genre=genre,
            album=album,
            file=mp3_file,
            track_number=track_number,
            year=year,
            lyrics=lyrics,
            search_aliases=search_aliases_combined
        )

        # ۸. متصل کردن ManyToMany آرتیست‌ها
        for name in artist_names:
            art_obj, _ = Artist.objects.get_or_create(name=name.strip())
            music.artists.add(art_obj)

        # ۹. ارسال نوتیفیکیشن برای فالورها
        followers = ArtistFollow.objects.filter(artist=artist)
        notifications = []
        for follow in followers:
            notifications.append(
                Notification(
                    user=follow.user,
                    title='آهنگ جدید',
                    message=f'{artist.name} آهنگ جدید "{music.title}" را منتشر کرد.',
                    url=reverse(
                        "music_detail",
                        kwargs={
                            "pk": music.id,
                            "slug_en": music.slug_en,
                        }
                    ))
            )
        Notification.objects.bulk_create(notifications)

        # ۱۰. استخراج و ذخیره کاور آرت
        cover = extract_cover(mp3_file)
        if cover:
            music.cover.save(cover.name, cover, save=True)
            if album and not album.cover:
                cover.seek(0)
                album.cover.save(cover.name, cover, save=True)

        TelegramFile.objects.create(
            file_id=file_id,
            music=music
        )

        print(f"✅ آهنگ '{display_title}' با موفقیت از تلگرام دریافت و ذخیره شد.")
        return True

    except Exception as e:
        print("❌ خطا در فرآیند پردازش و ذخیره فایل تلگرام:", e)
        return False
