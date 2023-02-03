import asyncio

from django.apps import AppConfig

from swipy_bot import application
from swipy_config import TELEGRAM_TOKEN, SWIPY_DJANGO_HOST


class SwipyAppConfig(AppConfig):  # pylint: disable=too-few-public-methods
    default_auto_field = "django.db.models.BigAutoField"
    name = "swipy_app"

    def ready(self) -> None:
        async def _init_swipy_bot():
            await application.initialize()

            webhook_url = f"{SWIPY_DJANGO_HOST}/{TELEGRAM_TOKEN}/"
            # TODO oleksandr: use secret_token parameter of set_webhook instead of the token in the url
            await application.bot.set_webhook(webhook_url)

        asyncio.get_event_loop().create_task(_init_swipy_bot())
