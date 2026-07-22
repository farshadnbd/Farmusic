from django.urls import path

from . import bot_views
from .views import *
from django.contrib.sitemaps.views import sitemap
from .sitemaps import MusicSitemap, ArtistSitemap, AlbumSitemap, GenreSitemap

sitemaps = {
    'musics': MusicSitemap,
    'artists': ArtistSitemap,
    'albums': AlbumSitemap,
    'genres': GenreSitemap,
}
urlpatterns = [
    path('', home, name='home'),
    path('music/<int:pk>/<str:slug_en>/', music_detail, name='music_detail'),
    path('download/<int:pk>/', download_music, name='download_music'),

    path('search/', search_music, name='search_music'),
    path('genre/<int:genre_id>/<str:slug_en>/', genre_musics, name='genre_musics'),
    path('popular/', popular_musics, name='popular_musics'),

    path('artists/', artists_list, name='artists_list'),
    path('artist/<int:artist_id>/<str:slug_en>/', artist_detail, name='artist_detail'),
    path('about/', about, name='about'),
    path('like/<int:music_id>/', toggle_like, name='toggle_like'),
    path('comment/<int:music_id>/', add_comment, name='add_comment'),
    path('reply/<int:comment_id>/', reply_comment, name='reply_comment'),
    path('delete-comment/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('favorites/', favorite_musics, name='favorites'),
    path('search-suggestions/', search_suggestions, name='search_suggestions'),

    path('album/<int:album_id>/download/', download_album, name='download_album'),
    path('album/<int:album_id>/<str:slug_en>/', album_detail, name='album_detail'),

    path('artist/<int:artist_id>/follow', toggle_follow_artist, name='toggle_follow_artist'),
    path('playlists/', playlists, name='playlists'),
    path('playlists/create/', create_playlist, name='create_playlist'),
    path('playlist/add/<int:music_id>/', add_to_playlist, name='add_to_playlist'),
    path('playlist/<int:playlist_id>/', playlist_detail, name='playlist_detail'),
    path('playlist/<int:playlist_id>/remove/<int:music_id>/', remove_from_playlist, name='remove_from_playlist'),
    path('playlist/<int:playlist_id>/delete/', delete_playlist, name='delete_playlist'),
    path('playlist/<int:playlist_id>/edit/', edit_playlist, name='edit_playlist'),
    path('comment/<int:comment_id>/report/', report_comment, name='report_comment'),
    path('sitemap-main.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('telegram-webhook-secret-99/', bot_views.telegram_webhook, name='telegram_webhook'),
    path("api/import-music/", import_music, name="import_music"),
    path("api/check-file/", check_file, name="check_file"),
]

handler404 = 'music.views.custom_404'
