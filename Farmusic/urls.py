from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('music.urls')), # 👈 تمام مسیرهای موزیک، سایتمپ و ربات اینجاست
    path('accounts/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    path('admin-dashboard/', include('dashboard.urls')),
    path('51475603.txt', lambda r: HttpResponse("51475603", content_type="text/plain")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )