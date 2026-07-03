from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload')

]
