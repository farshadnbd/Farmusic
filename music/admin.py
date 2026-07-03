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


# ۴. ثبت ادمین Album
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['admin_cover', 'title', 'artist', 'release_date']
    search_fields = ['title', 'artist__name']
    autocomplete_fields = ['artist']
    inlines = [MusicInline]

    def admin_cover(self, obj):
        if obj.cover:
            return format_html(
                '<img src="{0}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;" />',
                obj.cover.url)
        return "بدون کاور"

    admin_cover.short_description = 'کاور'


# ۵. ثبت ادمین اصلی Music (اضافه شدن خواننده به جدول نمایش)
@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    # فیلد artist (خواننده اصلی) به لیست نمایش اضافه شد
    list_display = ['admin_cover', 'title', 'artist', 'genre', 'search_aliases', 'is_vip', 'download_count',
                    'created_at', 'row_actions']

    # فیلد title به خاطر تداخل دکمه‌های لینک ادمین، از list_editable حذف شد تا خطایی رخ ندهد
    list_editable = ['genre', 'search_aliases', 'is_vip']
    list_display_links = ['admin_cover', 'title']

    list_filter = ['is_vip', 'genre', 'created_at']
    search_fields = ['title', 'artist__name', 'album__title', 'search_aliases']
    ordering = ['-created_at']
    autocomplete_fields = ['artist', 'genre', 'album']

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
            '#changelist .results table { width: 100% !important; min-width: 1300px !important; }'
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