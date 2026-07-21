from django.shortcuts import render, redirect, get_object_or_404
from dashboard.utils import generate_album_zip
from .models import Music, Genre, Artist, Like, Comment, Album, ArtistFollow, Playlist, CommentReport
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from accounts.models import Subscription
from django.core.paginator import Paginator
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, HttpResponse
import os
import mimetypes
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


def home(request):
    musics = Music.objects.select_related('artist', 'genre', 'album').order_by('-created_at')
    music_count = Music.objects.count()
    artist_count = Artist.objects.count()
    genre_count = Genre.objects.count()
    total_downloads = (Music.objects.aggregate(total=Sum('download_count'))['total'] or 0)
    paginator = Paginator(musics, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    latest_albums = Album.objects.order_by('-created_at')[:8]
    user_has_vip = False

    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
            user_has_vip = (
                    subscription.active and
                    subscription.expire_date >= timezone.now()
            )
        except Subscription.DoesNotExist:
            pass

    return render(
        request,
        'music/home.html',
        {'musics': musics, 'music_count': music_count, 'artist_count': artist_count, 'genre_count': genre_count,
         'total_downloads': total_downloads, 'page_obj': page_obj, 'latest_albums': latest_albums,
         "user_has_vip": user_has_vip, })


def music_detail(request, pk, slug_en=None):
    music = get_object_or_404(
        Music.objects.select_related('artist', 'genre', 'album'),
        pk=pk
    )

    if slug_en is None or (music.slug_en and music.slug_en != slug_en):
        return redirect(
            'music_detail',
            pk=music.id,
            slug_en=music.slug_en or 'music',
            permanent=True
        )

    music.views_count += 1
    music.save(update_fields=['views_count'])

    can_download = True
    related_musics = (
        Music.objects.select_related('artist', 'genre')
        .filter(artist=music.artist)
        .exclude(id=music.id)[:6]
    )
    comments = Comment.objects.filter(
        music=music,
        parent__isnull=True
    ).order_by('-created_at')

    playlists = []
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(user=request.user)

    # 🟢 محاسبه وضعیت اشتراک برای اسکریپت سراسری VIP
    user_has_vip = False
    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
            if subscription.active and subscription.expire_date > timezone.now():
                user_has_vip = True
                can_download = True
        except Subscription.DoesNotExist:
            pass

    # این شرط قدیمی رو چون منطقش رو بالا ادغام کردیم، می‌تونی برای تمیزی کد اینطوری بنویسی:
    if music.is_vip and not user_has_vip:
        can_download = False

    return render(
        request,
        'music/detail.html',
        {
            'music': music,
            'can_download': can_download,
            'related_musics': related_musics,
            'comments': comments,
            'playlists': playlists,
            'user_has_vip': user_has_vip,  # 👈 اضافه شد
        }
    )


def download_music(request, pk):
    music = get_object_or_404(Music, pk=pk)

    # ۱. بررسی اشتراک VIP برای کاربر
    if music.is_vip:
        if not request.user.is_authenticated:
            messages.error(request, 'ابتدا وارد حساب کاربری شوید.')
            return redirect('login')

        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.active or subscription.expire_date < timezone.now():
                messages.error(request, 'اشتراک شما فعال نیست.')
                return redirect('buy_subscription')
        except Subscription.DoesNotExist:
            messages.error(request, 'برای دانلود اشتراک تهیه کنید.')
            return redirect('buy_subscription')

    # پیدا کردن آدرس فایل
    file_url = music.audio_url if music.audio_url else (music.file.url if music.file else None)
    if not file_url:
        messages.error(request, 'فایل صوتی یافت نشد.')
        return redirect('home')

    # ۲. مدیریت آمار دانلود و اجبار به دانلود مستقیم
    if request.GET.get('download') == 'true':
        music.download_count += 1
        music.save(update_fields=['download_count'])

        # ترفند: اضافه کردن کوری استرینگ برای مجبور کردن بعضی هاست‌های دانلود به دانلود مستقیم
        # اگر هاست دانلود شما پارامتر دیسپوزیشن را ساپورت کند (مثل ?dl=1 یا ?download=1) آن را اینجا اضافه کنید:
        # if "?" in file_url:
        #     file_url += "&dl=1"
        # else:
        #     file_url += "?dl=1"

    # ۳. ریدایرکت به هاست دانلود
    return redirect(file_url)


def normalize_search_text(text):
    """
    نرمال‌سازی خیلی سبک برای جستجو:
    - trim
    - lowercase
    - تبدیل فاصله‌های چندگانه به یک فاصله
    """
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


def search_music(request):
    query = normalize_search_text(request.GET.get('q', ''))
    musics = Music.objects.none()

    if query:
        query_slug = query.replace(' ', '-')

        musics = (
            Music.objects
            .select_related('artist', 'genre', 'album')
            .filter(
                Q(title__icontains=query) |
                Q(slug_en__icontains=query_slug) |
                Q(search_aliases__icontains=query) |

                Q(artist__name__icontains=query) |
                Q(artist__slug_en__icontains=query_slug) |
                Q(artist__search_aliases__icontains=query) |

                Q(album__title__icontains=query) |
                Q(album__slug_en__icontains=query_slug) |
                Q(album__search_aliases__icontains=query) |

                Q(genre__name__icontains=query) |
                Q(genre__slug_en__icontains=query_slug) |
                Q(genre__search_aliases__icontains=query)
            )
            .distinct()
            .order_by('-created_at')
        )

    return render(request, 'music/search.html', {
        'musics': musics,
        'query': request.GET.get('q', '').strip()
    })


# اصلاح شد: تغییر پارامتر ورودی از name_en به slug_en برای یکپارچگی مسیرها
def genre_musics(request, genre_id, slug_en=None):
    genre = get_object_or_404(Genre, id=genre_id)

    if slug_en is None or (genre.slug_en and genre.slug_en != slug_en):
        return redirect('genre_musics', genre_id=genre.id, slug_en=genre.slug_en or 'genre', permanent=True)

    musics = Music.objects.filter(genre=genre).order_by('-created_at')
    paginator = Paginator(musics, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🟢 محاسبه وضعیت اشتراک برای صفحه ژانر
    user_has_vip = False
    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
            user_has_vip = subscription.active and subscription.expire_date >= timezone.now()
        except Subscription.DoesNotExist:
            pass

    return render(
        request,
        'music/genre_musics.html',
        {
            'genre': genre,
            'musics': musics,
            'page_obj': page_obj,
            'user_has_vip': user_has_vip  # 👈 اضافه شد
        }
    )


def popular_musics(request):
    # گرفتن نوع مرتب‌سازی از کوئری‌استرینگ (پیش‌فرض روی دانلود قرار دارد)
    sort_by = request.GET.get('sort', 'download')

    if sort_by == 'view':
        # مرتب‌سازی بر اساس بیشترین بازدید
        musics = Music.objects.order_by('-views_count', '-created_at')
    elif sort_by == 'like':
        # مرتب‌سازی بر اساس بیشترین لایک
        from django.db.models import Count
        musics = Music.objects.annotate(likes_total=Count('likes')).order_by('-likes_total', '-created_at')
    else:
        # پیش‌فرض: مرتب‌سازی بر اساس بیشترین دانلود
        musics = Music.objects.order_by('-download_count', '-created_at')

    paginator = Paginator(musics, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🟢 محاسبه وضعیت اشتراک برای صفحه محبوب‌ترین‌ها
    user_has_vip = False
    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
            user_has_vip = subscription.active and subscription.expire_date >= timezone.now()
        except Subscription.DoesNotExist:
            pass

    return render(request, 'music/popular.html', {
        'musics': musics,
        'page_obj': page_obj,
        'current_sort': sort_by,
        'user_has_vip': user_has_vip  # 👈 اضافه شد
    })


def artists_list(request):
    # دریافت نوع مرتب‌سازی از آدرس بار (پیش‌فرض روی جدیدترین‌ها یا معمولی)
    sort_by = request.GET.get('sort', 'default')

    if sort_by == 'alphabet':
        # مرتب‌سازی بر اساس حروف الفبای نام خواننده (صعودی)
        artists = Artist.objects.all().order_by('name')
    elif sort_by == 'popular':
        # در صورت تمایل برای سورت بر اساس فالوور (در مدل شما پراپرتی followers_count وجود دارد)
        # برای سورت بهینه جنگو، از Count روی ریلیشن معکوس استفاده می‌کنیم:
        from django.db.models import Count
        artists = Artist.objects.annotate(total_followers=Count('artistfollow')).order_by('-total_followers', 'name')
    else:
        # پیش‌فرض: مرتب‌سازی معمولی یا بر اساس جدیدترین‌ها
        artists = Artist.objects.all().order_by('-id')

    paginator = Paginator(artists, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'music/artists.html', {
        'page_obj': page_obj,
        'current_sort': sort_by
    })


def artist_detail(request, artist_id, slug_en=None):
    artist = get_object_or_404(Artist, id=artist_id)

    if slug_en is None or (artist.slug_en and artist.slug_en != slug_en):
        correct_slug = artist.slug_en or "artist"
        return redirect('artist_detail', artist_id=artist.id, slug_en=correct_slug, permanent=True)

    musics = Music.objects.filter(Q(artists=artist) | Q(artist=artist)).distinct().order_by('-created_at')
    paginator = Paginator(musics, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    albums = Album.objects.filter(artist=artist).order_by('-created_at')
    singles = Music.objects.filter(Q(artists=artist) | Q(artist=artist), album__isnull=True).distinct().order_by(
        '-created_at')

    # 🟢 محاسبه وضعیت اشتراک برای صفحه هنرمند
    user_has_vip = False
    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
            user_has_vip = subscription.active and subscription.expire_date >= timezone.now()
        except Subscription.DoesNotExist:
            pass

    is_following = False
    if request.user.is_authenticated:
        is_following = ArtistFollow.objects.filter(user=request.user, artist=artist).exists()

    return render(
        request,
        'music/artist_detail.html',
        {
            'artist': artist,
            'musics': musics,
            'page_obj': page_obj,
            'albums': albums,
            'singles': singles,
            'is_following': is_following,
            'user_has_vip': user_has_vip  # 👈 اضافه شد
        }
    )


def about(request):
    return render(request, 'music/about.html')


def custom_404(request, exception):
    return render(request, '404.html', status=404)


@login_required
def toggle_like(request, music_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "درخواست نامعتبر است."}, status=400)

    music = get_object_or_404(Music, id=music_id)
    like_qs = Like.objects.filter(user=request.user, music=music)

    if like_qs.exists():
        like_qs.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, music=music)
        liked = True

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes_count": music.likes_count,
        "music_id": music.id,
    })


# views.py

@login_required
def add_comment(request, music_id):
    music = get_object_or_404(Music, id=music_id)

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            comment = Comment.objects.create(music=music, user=request.user, text=text)

            # بررسی درخواست آژاکس
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                avatar_url = request.user.profile.avatar.url if hasattr(request.user,
                                                                        'profile') and request.user.profile.avatar else '/static/images/default-avatar.png'
                return JsonResponse({
                    "success": True,
                    "comment_id": comment.id,
                    "username": comment.user.username,
                    "avatar_url": avatar_url,
                    "text": comment.text,
                    "created_at": comment.created_at.strftime("%Y/%m/%d - %H:%M"),
                    "comments_count": Comment.objects.filter(music=music, parent__isnull=True).count()
                    # تعداد کل کامنت‌های اصلی
                })

    return redirect('music_detail', pk=music.id, slug_en=music.slug_en)


@login_required
def reply_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            reply = Comment.objects.create(
                music=parent_comment.music,
                user=request.user,
                text=text,
                parent=parent_comment
            )

            # بررسی درخواست آژاکس
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                avatar_url = request.user.profile.avatar.url if hasattr(request.user,
                                                                        'profile') and request.user.profile.avatar else '/static/images/default-avatar.png'
                return JsonResponse({
                    "success": True,
                    "reply_id": reply.id,
                    "username": reply.user.username,
                    "avatar_url": avatar_url,
                    "text": reply.text,
                    "created_at": reply.created_at.strftime("%Y/%m/%d")
                })

    return redirect(
        'music_detail',
        pk=parent_comment.music.id,
        slug_en=parent_comment.music.slug_en or "music"
    )


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    music = comment.music

    if comment.user == request.user:
        comment.delete()

    return redirect(
        'music_detail',
        pk=music.id,
        slug_en=music.slug_en or "music"
    )


@login_required
def favorite_musics(request):
    musics = (
        Music.objects
        .filter(likes__user=request.user)
        .select_related('artist', 'genre', 'album')
        .distinct()
    )

    # 🟢 محاسبه وضعیت اشتراک برای صفحه علاقه‌مندی‌ها
    user_has_vip = False
    try:
        subscription = Subscription.objects.get(user=request.user)
        user_has_vip = subscription.active and subscription.expire_date >= timezone.now()
    except Subscription.DoesNotExist:
        pass

    return render(
        request,
        'music/favorites.html',
        {
            'musics': musics,
            'user_has_vip': user_has_vip  # 👈 اضافه شد
        }
    )


def search_suggestions(request):
    q = normalize_search_text(request.GET.get('q', ''))
    if not q:
        return JsonResponse([], safe=False)

    query_slug = q.replace(' ', '-')

    musics = (
        Music.objects
        .select_related('artist')
        .filter(
            Q(title__icontains=q) |
            Q(slug_en__icontains=query_slug) |
            Q(search_aliases__icontains=q) |

            Q(artist__name__icontains=q) |
            Q(artist__slug_en__icontains=query_slug) |
            Q(artist__search_aliases__icontains=q)
        )
        .distinct()[:5]
    )

    artists = Artist.objects.filter(
        Q(name__icontains=q) |
        Q(slug_en__icontains=query_slug) |
        Q(search_aliases__icontains=q)
    ).distinct()[:5]

    albums = Album.objects.filter(
        Q(title__icontains=q) |
        Q(slug_en__icontains=query_slug) |
        Q(search_aliases__icontains=q) |

        Q(artist__name__icontains=q) |
        Q(artist__slug_en__icontains=query_slug) |
        Q(artist__search_aliases__icontains=q)
    ).distinct()[:5]

    genres = Genre.objects.filter(
        Q(name__icontains=q) |
        Q(slug_en__icontains=query_slug) |
        Q(search_aliases__icontains=q)
    ).distinct()[:4]

    data = []

    # اول آرتیست‌ها
    for artist in artists:
        data.append({
            'type': 'artist',
            'id': artist.id,
            'name': artist.name,
            'slug': artist.slug_en or 'artist'
        })

    # بعد آلبوم‌ها
    for album in albums:
        data.append({
            'type': 'album',
            'id': album.id,
            'title': album.title,
            'artist': album.artist.name if album.artist else '',
            'slug': album.slug_en or 'album'
        })

    # بعد ژانرها
    for genre in genres:
        data.append({
            'type': 'genre',
            'id': genre.id,
            'name': genre.name,
            'slug': genre.slug_en or 'genre'
        })

    # بعد موزیک‌ها
    for music in musics:
        data.append({
            'type': 'music',
            'id': music.id,
            'title': music.title,
            'artist': music.artist.name if music.artist else 'ناشناس',
            'slug': music.slug_en or 'music'
        })

    return JsonResponse(data, safe=False)


def album_detail(request, album_id, slug_en=None):
    album = get_object_or_404(Album, id=album_id)

    if slug_en is None or (album.slug_en and album.slug_en != slug_en):
        return redirect(
            'album_detail',
            album_id=album.id,
            slug_en=album.slug_en or 'album',
            permanent=True
        )

    musics = Music.objects.filter(album=album).order_by('track_number', 'id')

    return render(
        request,
        'music/album_detail.html',
        {
            'album': album,
            'musics': musics
        }
    )


@login_required
def download_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)

    try:
        subscription = Subscription.objects.get(user=request.user)
        if not subscription.active or subscription.expire_date < timezone.now():
            return redirect("buy_subscription")
    except Subscription.DoesNotExist:
        return redirect("buy_subscription")

    if not album.zip_file:
        generate_album_zip(album)
        album.refresh_from_db()

    return FileResponse(album.zip_file.open("rb"), as_attachment=True, filename=f"{album.title}.zip")


@login_required
def toggle_follow_artist(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    follow = ArtistFollow.objects.filter(user=request.user, artist=artist)

    if follow.exists():
        follow.delete()
    else:
        ArtistFollow.objects.create(user=request.user, artist=artist)

    return redirect(
        'artist_detail',
        artist_id=artist.id,
        slug_en=artist.slug_en or 'artist'
    )


@login_required
def playlists(request):
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'music/playlists.html', {'playlists': playlists})


@login_required
def create_playlist(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            Playlist.objects.create(user=request.user, title=title)
        return redirect('playlists')

    return render(request, 'music/create_playlist.html')


@login_required
def add_to_playlist(request, music_id):
    music = get_object_or_404(Music, id=music_id)

    if request.method == "POST":
        playlist_id = request.POST.get('playlist_id')
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        playlist.musics.add(music)

    return redirect('music_detail', pk=music.id, slug_en=music.slug_en)


@login_required
def playlist_detail(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    musics = playlist.musics.all()

    return render(request, 'music/playlist_detail.html', {'playlist': playlist, 'musics': musics, })


@login_required
def remove_from_playlist(request, playlist_id, music_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    music = get_object_or_404(Music, id=music_id)
    playlist.musics.remove(music)

    return redirect('playlist_detail', playlist_id=playlist_id)


@login_required
def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)

    if request.method == 'POST':
        playlist.delete()
        return redirect('playlists')

    return redirect('playlist_detail', playlist_id=playlist_id)


@login_required
def edit_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            playlist.title = title
            playlist.save()
            return redirect('playlist_detail', playlist.id)

    return render(request, 'music/edit_playlist.html', {'playlist': playlist})


@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        CommentReport.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'reason': reason}
        )
        return redirect(
            'music_detail',
            pk=comment.music.id,
            slug_en=comment.music.slug_en or "music"
        )

    return render(request, 'music/report_comment.html', {'comment': comment})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


SECRET = "farmusic-secret"


@csrf_exempt
@require_POST
def import_music(request):
    try:
        data = json.loads(request.body)

        if data.get("secret") != SECRET:
            return JsonResponse({"error": "unauthorized"},status=403)

        artist, _ = Artist.objects.get_or_create(name=data["artist"])

        genre = None
        if data.get("genre"):
            genre, _ = Genre.objects.get_or_create(name=data["genre"])

        album = None
        if data.get("album"):
            album, _ = Album.objects.get_or_create(title=data["album"], artist=artist)

        music = Music.objects.create(
            title=data["title"],
            artist=artist,
            album=album,
            genre=genre,
            audio_url=data["audio_url"],
            cover_url=data.get("cover_url"),  # 👈 این خط را اضافه کن
            file="placeholder.mp3",
            lyrics=data.get("lyrics") or "",
            year=data.get("year"),
            track_number=data.get("track_number"),
        )

        return JsonResponse({"ok": True,"music_id": music})

    except Exception as e:
        return JsonResponse({"ok": False,"error": str(e)}, status=500)
