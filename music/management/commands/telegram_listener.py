import time

from django.core.management.base import BaseCommand

from music.telegram_polling import check_updates


class Command(BaseCommand):
    help = "Telegram Listener"

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("🎵 Telegram Listener Started"))

        while True:
            check_updates()
            time.sleep(5)