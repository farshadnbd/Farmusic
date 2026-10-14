import random
from django.core.management.base import BaseCommand
from music.models import Music  # [cite: 3]


class Command(BaseCommand):
    help = 'افزایش متناسب و رندوم تعداد بازدید و دانلود آهنگ‌ها'

    def add_arguments(self, parser):
        parser.add_argument('--min-views', type=int, default=50, help='حداقل بازدید اضافه‌شونده')
        parser.add_argument('--max-views', type=int, default=10000, help='حداکثر بازدید اضافه‌شونده')

    def handle(self, *args, **options):
        min_v = options['min_views']
        max_v = options['max_views']
        musics = Music.objects.all()  # [cite: 3]
        count = musics.count()

        self.stdout.write(f"🚀 در حال افزایش متناسب آمار برای {count} آهنگ...")

        for music in musics:
            # ۱. تولید بازدید رندوم در بازه مشخص‌شده
            rand_views = random.randint(min_v, max_v)

            # ۲. تعیین تعداد دانلود متناسب با بازدید (بین ۳۰٪ تا ۶۰٪ تعداد بازدیدها)
            download_ratio = random.uniform(0.6, 0.9)
            rand_downloads = int(rand_views * download_ratio)

            music.views_count += rand_views  # [cite: 3]
            music.download_count += rand_downloads  # [cite: 3]
            music.save(update_fields=['views_count', 'download_count'])  # [cite: 3]

        self.stdout.write(self.style.SUCCESS(f"✅ آمار بازدید و دانلود با تناسب واقعی به‌روزرسانی شد!"))