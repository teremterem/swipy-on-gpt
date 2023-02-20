import asyncio
import json
from datetime import datetime
from functools import wraps

from django.http import HttpResponse, HttpRequest
from telegram import Update

from swipy_app.models import TelegramUpdate, SwipyUser
from swipy_bot.swipy_bot import application, UPDATE_DB_MODELS_VOLATILE_CACHE


async def health_check(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    return HttpResponse("Hello, world!")


def csrf_exempt_async(view_func):
    async def wrapped_view(*args, **kwargs):
        return await view_func(*args, **kwargs)

    wrapped_view.csrf_exempt = True
    return wraps(view_func)(wrapped_view)


@csrf_exempt_async
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
    arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

    async def _process_update() -> None:
        telegram_update_dict = json.loads(request.body)
        telegram_update = Update.de_json(telegram_update_dict, application.bot)

        # TODO oleksandr: shouldn't it be telegram_user_id + telegram_chat_id ?
        swipy_user = None
        if telegram_update.effective_chat:
            # TODO oleksandr: is select_related("current_conversation") only way to handle lazy properties in async ?
            swipy_user = (
                await SwipyUser.objects.filter(chat_telegram_id=telegram_update.effective_chat.id)
                .select_related("current_conversation")
                .afirst()
            )

            if not swipy_user:
                first_name = None
                full_name = None
                if telegram_update.effective_user:
                    first_name = telegram_update.effective_user.first_name
                    full_name = telegram_update.effective_user.full_name

                swipy_user = await SwipyUser.objects.acreate(
                    chat_telegram_id=telegram_update.effective_chat.id,
                    first_name=first_name,
                    full_name=full_name,
                )

        tg_update_in_db = await TelegramUpdate.objects.acreate(
            update_telegram_id=telegram_update.update_id,
            swipy_user=swipy_user,
            arrival_timestamp_ms=arrival_timestamp_ms,
            payload=telegram_update_dict,
        )
        UPDATE_DB_MODELS_VOLATILE_CACHE[id(telegram_update)] = tg_update_in_db

        await application.process_update(telegram_update)

    asyncio.get_event_loop().create_task(_process_update())
    # TODO oleksandr: is it a good idea to respond with 200 OK before the update is processed ?
    return HttpResponse("OK")
