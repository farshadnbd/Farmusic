"""
Django settings for Farmusic project.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# Security
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-9%2&sn_yi+tnwvy@nyxq+mn=^o@kx47j_e0fj!*!xwcalg3z#0")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = ["farmusic.liara.run", "127.0.0.1", "localhost", "farmusic.ir", "www.farmusic.ir", ]

# =========================
# Applications
# =========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    'music.apps.MusicConfig',
    'accounts',
    'payments',
    'dashboard',

    'easy_thumbnails',
    "django_cleanup.apps.CleanupConfig",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Farmusic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'music.context_processors.genres_processor',
                'accounts.context_processors.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'Farmusic.wsgi.application'

# =========================
# Database
# =========================

DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}

# =========================
# Password validation
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 4, }
    },
]

# =========================
# Internationalization
# =========================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# =========================
# Static & Media
# =========================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static", ]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"

if os.getenv("LIARA"):
    MEDIA_ROOT = "/media"
else:
    MEDIA_ROOT = BASE_DIR / "media"

# =========================
# Email
# =========================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "farmusicbackups@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "ylmocaelvifbwspb")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Farmusic <farmusicbackups@gmail.com>")

# =========================
# Easy Thumbnails
# =========================

THUMBNAIL_ALIASES = {"": {"music_card": {"size": (400, 400), "crop": True, "quality": 85, },
                          "music_detail": {"size": (700, 700), "crop": True, "quality": 90, },
                          "artist_avatar": {"size": (300, 300), "crop": True, "quality": 90, },
                          "album_cover": {"size": (500, 500), "crop": True, "quality": 88, }, }}

# =========================
# Telegram
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8371153857:AAF3YWVelognCWjb5blJpI3cXp4sLOyv6PQ")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004448617534")
SITE_URL = os.getenv("SITE_URL", "https://farmusic.ir").rstrip("/")
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID", "")
ZARINPAL_CALLBACK_URL = f"{SITE_URL}/payments/verify/"
FTP_HOST = os.environ.get("FTP_HOST", "dl.farmusic.com")
FTP_USER = os.environ.get("FTP_USER", "farmusic")
FTP_PASS = os.environ.get("FTP_PASS", "")  # این مقدار را در پنل لیارا ست می‌کنی
DOWNLOAD_BASE_URL = "dl.farmusic.ir"
TELEGRAM_API_BASE = "https://telegram.farmusic.ir"
