import asyncio

from django.apps import AppConfig

from swipy_bot import application
from swipy_config import TELEGRAM_TOKEN, SWIPY_DJANGO_BASE_URL


class SwipyAppConfig(AppConfig):  # pylint: disable=too-few-public-methods
    default_auto_field = "django.db.models.BigAutoField"
    name = "swipy_app"

    def ready(self) -> None:
        print("PRE-READY")
        print("PRE-READY")
        print("PRE-READY")
        print("PRE-READY")
        print("PRE-READY")

        async def _init_swipy_bot():
            print("PRE-INIT")
            print("PRE-INIT")
            print("PRE-INIT")
            print("PRE-INIT")
            print("PRE-INIT")
            await application.initialize()
            print("POST-INIT")
            print("POST-INIT")
            print("POST-INIT")
            print("POST-INIT")
            print("POST-INIT")

            webhook_url = f"{SWIPY_DJANGO_BASE_URL}/{TELEGRAM_TOKEN}/"
            # TODO oleksandr: use secret_token parameter of set_webhook instead of the token in the url
            await application.bot.set_webhook(webhook_url)
            print("HOOK-SET")
            print("HOOK-SET")
            print("HOOK-SET")
            print("HOOK-SET")
            print("HOOK-SET")

        asyncio.get_event_loop().create_task(_init_swipy_bot())
        print("POST-READY")
        print("POST-READY")
        print("POST-READY")
        print("POST-READY")
        print("POST-READY")
