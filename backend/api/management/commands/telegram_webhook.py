"""
Керування Telegram-вебхуком.

Приклади:
    python manage.py telegram_webhook set https://ke1fosao.pythonanywhere.com
    python manage.py telegram_webhook info
    python manage.py telegram_webhook delete
"""

import json

from django.core.management.base import BaseCommand

from api import telegram_bot as tg


class Command(BaseCommand):
    help = "Керування Telegram webhook: set <base_url> | info | delete"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["set", "info", "delete"])
        parser.add_argument("base_url", nargs="?", default="")

    def handle(self, *args, **opts):
        action = opts["action"]
        base_url = opts["base_url"]

        if not tg.is_configured():
            self.stderr.write(self.style.ERROR(
                "TELEGRAM_BOT_TOKEN не задано. Додайте його у backend/.env або у WSGI."))
            return
        if not tg.webhook_secret() and action == "set":
            self.stderr.write(self.style.ERROR(
                "TELEGRAM_WEBHOOK_SECRET не задано. Додайте довільний секрет у .env."))
            return

        if action == "set":
            if not base_url:
                self.stderr.write(self.style.ERROR(
                    "Вкажіть базовий URL, напр.: "
                    "python manage.py telegram_webhook set https://ke1fosao.pythonanywhere.com"))
                return
            result = tg.set_webhook(base_url)
        elif action == "info":
            result = tg.get_webhook_info()
        else:
            result = tg.delete_webhook()

        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get("ok"):
            self.stdout.write(self.style.SUCCESS("✓ Готово"))
