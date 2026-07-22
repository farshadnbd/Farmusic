import re
import threading

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from dashboard.utils import extract_cover, extract_metadata, extract_lyrics, generate_album_zip
from music.models import Music, Album, Artist, Comment, Genre, ArtistFollow
from music.utils import upload_to_ftp_and_clean  # 👈 امپورت تابع آپلود FTP شما
from accounts.models import Subscription, Notification


@staff_member_required
def admin_dashboard(request):
    context = {'users_count': User.objects.count(), 'musics_count': Music.objects.count(),
               'albums_count': Album.objects.count(),
               'artists_count': Artist.objects.count(), 'comments_count': Comment.objects.count(),
               'downloads_count': sum(Music.objects.values_list('download_count', flat=True)),
               'active_subscriptions': Subscription.objects.filter(active=True).count(),
               'latest_users': User.objects.order_by('-date_joined')[:5],
               'latest_musics': Music.objects.order_by('-created_at')
               }
    return render(request, 'dashboard/admin_dashboard.html', context)


@staff_member_required
def bulk_upload(request):
    if request.method == "POST":
        musics = request.FILES.getlist("musics")
        selected_genre_id = request.POST.get("genre")
        create_album_allowed = request.POST.get("create_album") == "on"
        ignore_unknown_genre = request.POST.get("ignore_unknown_genre") == "on"

        unknown_genre_files = []
        if not selected_genre_id or selected_genre_id == "auto":
            for mp3_file in musics:
                metadata = extract_metadata(mp3_file)
                genre_name = metadata.get("genre")
                if not genre_name or not genre_name.strip():
                    unknown_genre_files.append(mp3_file.name)

        if unknown_genre_files and not ignore_unknown_genre:
            files_list = ", ".join(unknown_genre_files)
            messages.warning(
                request,
                f"اخطار: ژانر آهنگ‌های روبرو یافت نشد (Unknown): [{files_list}]. "
                f"اگر مایل به آپلود با ژانر Unknown هستید، تیک زرد رنگ پایین را فعال کرده و مجدد دکمه آپلود را بزنید."
            )
            context = {"artists": Artist.objects.all(), "genres": Genre.objects.all(), }
            return render(request, "dashboard/bulk_upload.html", context)

        for mp3_file in musics:
            metadata = extract_metadata(mp3_file)

            raw_artist = metadata.get("artist") or "Unknown Artist"
            split_pattern = re.compile(r'\s+(?:ft\.?|feat\.?|&|/|and)\s+|[,\u060C]', re.IGNORECASE)
            artist_names = [name.strip() for name in split_pattern.split(raw_artist) if name.strip()]

            if not artist_names:
                artist_names = ["Unknown Artist"]

            main_artist_name = artist_names[0]
            artist, _ = Artist.objects.get_or_create(name=main_artist_name)
            search_aliases_combined = ", ".join(artist_names)

            title = (metadata["title"] or mp3_file.name.replace(".mp3", ""))
            if len(artist_names) > 1:
                featured_artists_str = ", ".join(artist_names[1:])
                display_title = f"{title} (Ft. {featured_artists_str})"
            else:
                display_title = title

            album_name = metadata.get("album")

            if selected_genre_id and selected_genre_id != "auto":
                try:
                    genre = Genre.objects.get(id=selected_genre_id)
                except Genre.DoesNotExist:
                    genre, _ = Genre.objects.get_or_create(name="Unknown")
            else:
                genre_name = metadata.get("genre")
                if genre_name:
                    for separator in ["&", "/", "and"]:
                        if separator in genre_name:
                            genre_name = genre_name.split(separator)[0]
                    genre, _ = Genre.objects.get_or_create(name=genre_name.strip())
                else:
                    genre, _ = Genre.objects.get_or_create(name="Unknown")

            album = None
            created = False
            if create_album_allowed and album_name:
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

            # ۱. ثبت اولیه موزیک روی دیسک موقت لیارا
            music = Music.objects.create(
                title=display_title, artist=artist, genre=genre, album=album, file=mp3_file,
                track_number=track_number, year=year, lyrics=lyrics,
                search_aliases=search_aliases_combined
            )

            for name in artist_names:
                art_obj, _ = Artist.objects.get_or_create(name=name.strip())
                music.artists.add(art_obj)

            # ۲. استخراج و ذخیره کاور آرت بدون استفاده از update_fields مشکل‌ساز
            cover = extract_cover(mp3_file)
            if cover:
                music.cover.save(cover.name, cover, save=False)
                if album and created and not album.cover:
                    cover.seek(0)
                    album.cover.save(cover.name, cover, save=True)

            # ۳. ذخیره نهایی و کامل آبجکت آهنگ (فایل صوتی و کاور با هم روی دیسک ثبت قطعی می‌شوند)
            music.save()

            # 🚀 ۴. ارسال مستقیم آهنگ به هاست دانلود با FTP شما در پس‌زمینه (Threading)
            if music.file and not music.audio_url:
                local_path = music.file.path
                music_id = music.id

                def start_ftp_upload(m_id, l_path):
                    # این تابع دقیقاً متصل به هاست FTP شما میشه و فایل رو منتقل می‌کنه
                    success = upload_to_ftp_and_clean(m_id, l_path)
                    if success:
                        try:
                            # ارسال موزیک به کانال تلگرام پس از آپلود موفق در هاست دانلود
                            from music.models import Music as MusicModel
                            from music.telegram import send_new_music_to_telegram
                            updated_music = MusicModel.objects.get(id=m_id)
                            send_new_music_to_telegram(updated_music)
                        except Exception as telegram_err:
                            print(f"Telegram automated notification failed: {telegram_err}")

                # اجرای پروسه آپلود FTP بدون معطل کردن فرانت‌اند
                threading.Thread(target=start_ftp_upload, args=(music_id, local_path)).start()

            # ۵. ارسال نوتیفیکیشن برای کاربران سایت
            followers = ArtistFollow.objects.filter(artist=artist)
            notifications = []
            for follow in followers:
                notifications.append(
                    Notification(
                        user=follow.user,
                        title='آهنگ جدید',
                        message=f'{artist.name} آهنگ جدید "{music.title}" را منتشر کرد.',
                        url=reverse("music_detail", kwargs={"pk": music.id, "slug_en": music.slug_en, })
                    )
                )
            Notification.objects.bulk_create(notifications)

            if album and album.zip_file:
                album.zip_file.delete(save=False)
                album.zip_file = None
                album.save()

        messages.success(request,
                         f"{len(musics)} آهنگ با موفقیت به همراه تفکیک خوانندگان اضافه و فرآیند انتقال به هاست دانلود آغاز شد.")
        return redirect('bulk_upload')

    context = {"artists": Artist.objects.all(), "genres": Genre.objects.all(), }
    return render(request, "dashboard/bulk_upload.html", context)