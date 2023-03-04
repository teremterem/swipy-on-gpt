import asyncio
import logging

from django.apps import AppConfig

from swipy_app.swipy_config import TELEGRAM_TOKEN, SWIPY_DJANGO_BASE_URL

logger = logging.getLogger(__name__)


class SwipyAppConfig(AppConfig):  # pylint: disable=too-few-public-methods
    default_auto_field = "django.db.models.BigAutoField"
    name = "swipy_app"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel
        from swipy_app.swipy_bot import application

        logger.info("SwipyAppConfig.ready() - entered")

        async def _init_swipy_bot():
            logger.info("SwipyAppConfig.ready() - preparing to init swipy bot")
            await application.initialize()
            logger.info("SwipyAppConfig.ready() - swipy bot initialized")

            webhook_url = f"{SWIPY_DJANGO_BASE_URL}/{TELEGRAM_TOKEN}/"
            # TODO oleksandr: use secret_token parameter of set_webhook instead of the token in the url
            await application.bot.set_webhook(webhook_url)
            logger.info("SwipyAppConfig.ready() - swipy bot webhook set")

        asyncio.get_event_loop().create_task(_init_swipy_bot())
        logger.info("SwipyAppConfig.ready() - exited")
