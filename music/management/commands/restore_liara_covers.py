import os
import requests
from PIL import Image, ImageOps
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from music.models import Music, Album


class Command(BaseCommand):
    help = 'بازیابی و دانلود مجدد کاورها روی دیسک لیارا برای آهنگ‌هایی که کاور محلی‌شان پاک شده است'

    def handle(self, *args, **options):
        # آهنگ‌هایی که cover_url دارند اما فایل محلی‌شان روی دیسک لیارا نیست
        musics_to_restore = Music.objects.exclude(cover_url='').exclude(cover_url__isnull=True)

        restored_count = 0
        skipped_count = 0

        self.stdout.write("🚀 شروع بررسی و بازیابی کاورها روی دیسک لیارا...")

        for music in musics_to_restore:
            # بررسی اینکه آیا فایل محلی واقعاً روی هارد وجود دارد یا خیر
            file_exists = music.cover and os.path.exists(music.cover.path)

            if file_exists:
                skipped_count += 1
                continue

            # چک کردن اینکه آیا آلبوم این آهنگ قبلاً کاور محلیِ معتبری روی دیسک دارد یا خیر (منطق اشتراک‌گذاری)
            if music.album and music.album.cover and os.path.exists(music.album.cover.path):
                music.cover = music.album.cover
                music.save(update_fields=['cover'])
                self.stdout.write(f"♻️ استفاده از کاور مشترک آلبوم برای آهنگ: {music.title}")
                restored_count += 1
                continue

            # اگر کاوری وجود ندارد، باید از طریق cover_url دانلود شود
            cover_url = music.cover_url
            self.stdout.write(f"📥 در حال دانلود و بازسازی کاور برای: {music.title}")

            try:
                response = requests.get(cover_url, timeout=20)
                if response.status_code == 200:
                    image_content = response.content
                    filename = f"cover_{music.id}.jpg"

                    # ذخیره موقت در فیلد ImageField
                    music.cover.save(filename, ContentFile(image_content), save=True)
                    local_cover = music.cover.path

                    # کراپ و فشرده‌سازی استاندارد (۴۰۰ در ۴۰۰)
                    img = Image.open(local_cover).convert("RGB")
                    img = ImageOps.fit(img, (400, 400), Image.Resampling.LANCZOS)
                    img.save(local_cover, "JPEG", quality=85, optimize=True)

                    # اگر آهنگ آلبوم دارد، این کاور را به عنوان کاور اصلی آلبوم هم ثبت کن
                    if music.album and not music.album.cover:
                        music.album.cover = music.cover
                        music.album.save(update_fields=['cover'])

                    restored_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ بازسازی موفق کاور: {music.title}"))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ لینک کاور نامعتبر بود برای: {music.title} (Status: {response.status_code})"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ خطا در دانلود کاور {music.title}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 پایان عملیات! تعداد {restored_count} کاور بازیابی و روی لیارا ذخیره شد. ({skipped_count} آهنگ از قبل کاور داشتند)."))