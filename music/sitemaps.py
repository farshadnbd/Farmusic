from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Music, Artist, Album, Genre


class MusicSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Music.objects.all().select_related('artist', 'genre', 'album')

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        slug = obj.slug_en if obj.slug_en else "music"
        return reverse('music_detail', args=[obj.id, slug])


class ArtistSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Artist.objects.all()

    def location(self, obj):
        slug = obj.slug_en if obj.slug_en else "artist"
        return reverse('artist_detail', args=[obj.id, slug])


class AlbumSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Album.objects.all().select_related('artist')

    def location(self, obj):
        slug = obj.slug_en if obj.slug_en else "album"
        return reverse('album_detail', args=[obj.id, slug])


class GenreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Genre.objects.all()

    def location(self, obj):
        slug = obj.slug_en if obj.slug_en else "genre"
        return reverse('genre_musics', args=[obj.id, slug])