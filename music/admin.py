from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from accounts.models import Notification
from .models import Music, Artist, Genre, Comment, Album, Playlist, ArtistFollow, CommentReport
from django.urls import reverse

# ثبت مدل‌های ساده
admin.site.register(Comment)
admin.site.register(Playlist)


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'created_at']
    search_fields = ['reason', 'user__username']


# ۱. تعریف Inlineها
class MusicInline(admin.TabularInline):
    model = Music
    fields = ['title', 'file', 'track_number', 'is_vip']
    extra = 1


class AlbumInline(admin.TabularInline):
    model = Album
    extra = 1


# ۲. ثبت ادمین Artist
@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['admin_image', 'image', 'name', 'country', 'search_aliases', 'followers_count', 'artist_actions']
    list_editable = ['image', 'search_aliases']
    list_display_links = ['name']
    search_fields = ['name', 'search_aliases']
    inlines = [AlbumInline]

    def admin_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{0}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.image.url)
        return "بدون عکس"

    admin_image.short_description = 'پیش‌نمایش'

    def artist_actions(self, obj):
        return format_html(
            '<button type="submit" name="_save" class="button" style="padding: 4px 10px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer; display: inline-block; vertical-align: middle;">💾 ذخیره</button>'
            '<a class="deletelink" href="{0}/delete/" style="padding: 5px 10px; background: #ba2121; color: white; border-radius: 4px; text-decoration: none; font-size: 11px; display: inline-block; margin-right: 12px; vertical-align: middle;">🗑️ حذف</a>',
            obj.pk
        )

    artist_actions.short_description = 'عملیات سریع'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['extracss'] = mark_safe(
            '<style>'
            '#changelist .results { overflow-x: auto !important; display: block !important; width: 100% !important; padding-bottom: 12px !important; }'
            '#changelist .results table { width: 100% !important; min-width: 1200px !important; }'
            '#changelist .results::-webkit-scrollbar { height: 9px !important; }'
            '#changelist .results::-webkit-scrollbar-track { background: #f1f1f1 !important; border-radius: 5px !important; }'
            '#changelist .results::-webkit-scrollbar-thumb { background: #79aec8 !important; border-radius: 5px !important; }'
            '#changelist .results::-webkit-scrollbar-thumb:hover { background: #417690 !important; }'
            '</style>'
        )
        return super().changelist_view(request, extra_context=extra_context)


# ۳. ثبت ادمین Genre
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug_en']
    search_fields = ['name']


# ۴. ثبت ادمین Album (با قابلیت جستجوی هنرمند)
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['admin_cover', 'title', 'artist', 'release_date']
    search_fields = ['title', 'artist__name']
    autocomplete_fields = ['artist']  # 👈 امکان جستجوی نام هنرمند هنگام انتخاب آلبوم
    inlines = [MusicInline]

    def admin_cover(self, obj):
        if obj.cover:
            return format_html(
                '<img src="{0}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;" />',
                obj.cover.url)
        return "بدون کاور"

    admin_cover.short_description = 'کاور'


# ۵. ثبت ادمین اصلی Music
@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    # اضافه شدن آمار بازدید و دانلود به جدول لیست برای ویرایش مستقیم
    list_display = ['admin_cover', 'title', 'artist', 'album', 'genre', 'views_count', 'download_count', 'is_vip',
                    'is_trending', 'row_actions']

    # امکان تغییر مستقیم این فیلدها از صفحه اول
    list_editable = ['views_count', 'download_count', 'is_vip', 'is_trending']
    list_display_links = ['admin_cover', 'title']

    list_filter = ['is_vip', 'genre', 'created_at']

    # 👈 امکان سرچ پیشرفته بین آلبوم، خواننده اصلی، نام آهنگ و نام‌های جایگزین
    search_fields = ['title', 'artist__name', 'artists__name', 'album__title', 'search_aliases']

    # 👈 فیلدهای جستجوی سریع در حالت انتخاب (Autocomplete) برای آلبوم و خوانندگان
    autocomplete_fields = ['artist', 'artists', 'album', 'genre']

    # مرتب‌سازی پیش‌فرض (جدیدترین‌ها در ابتدا، اما با قابلیت سفارشی‌سازی)
    ordering = ['-created_at']

    def row_actions(self, obj):
        return format_html(
            '<button type="submit" name="_save" class="button" style="padding: 4px 10px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer; display: inline-block; vertical-align: middle;">💾 ذخیره</button>'
            '<a class="deletelink" href="{0}/delete/" style="padding: 5px 10px; background: #ba2121; color: white; border-radius: 4px; text-decoration: none; font-size: 11px; display: inline-block; margin-right: 12px; vertical-align: middle;">🗑️ حذف</a>',
            obj.pk
        )

    row_actions.short_description = 'عملیات سریع'

    def admin_cover(self, obj):
        if obj.cover:
            return format_html(
                '<img src="{0}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover; cursor: pointer;" />',
                obj.cover.url)
        return "📁 ورود"

    admin_cover.short_description = 'کاور'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['extracss'] = mark_safe(
            '<style>'
            '#changelist .results { overflow-x: auto !important; display: block !important; width: 100% !important; padding-bottom: 12px !important; }'
            '#changelist .results table { width: 100% !important; min-width: 1400px !important; }'
            '#changelist .results::-webkit-scrollbar { height: 9px !important; }'
            '#changelist .results::-webkit-scrollbar-track { background: #f1f1f1 !important; border-radius: 5px !important; }'
            '#changelist .results::-webkit-scrollbar-thumb { background: #79aec8 !important; border-radius: 5px !important; }'
            '#changelist .results::-webkit-scrollbar-thumb:hover { background: #417690 !important; }'
            '</style>'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            followers = ArtistFollow.objects.filter(artist=obj.artist)
            for follow in followers:
                Notification.objects.create(
                    user=follow.user,
                    title='آهنگ جدید',
                    message=f'{obj.artist.name} آهنگ جدید "{obj.title}" را منتشر کرد.',
                    url=reverse(
                        "music_detail",
                        kwargs={
                            "pk": obj.id,
                            "slug_en": obj.slug_en,
                        }
                    )
                )
