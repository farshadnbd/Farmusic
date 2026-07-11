from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from music.sitemaps import (
MusicSitemap,
ArtistSitemap,
AlbumSitemap,
)

sitemaps = {
'music': MusicSitemap,
'artist': ArtistSitemap,
'album': AlbumSitemap,
}

urlpatterns = [
path('admin/', admin.site.urls),
path('', include('music.urls')),
path('accounts/', include('accounts.urls')),
path('payments/', include('payments.urls')),
path('admin-dashboard/', include('dashboard.urls')),
path('51475603.txt', lambda r: HttpResponse("51475603", content_type="text/plain")),

path(
    'sitemap.xml',
    sitemap,
    {'sitemaps': sitemaps},
    name='django.contrib.sitemaps.views.sitemap'
),

]

if settings.DEBUG:
    urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
    )