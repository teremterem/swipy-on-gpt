import asyncio
import json
from datetime import datetime
from functools import wraps

from asgiref.sync import sync_to_async
from django.http import HttpResponse, HttpRequest
from telegram import Update

from swipy_app.models import TelegramUpdate
from swipy_bot import application, UPDATE_DB_MODELS_VOLATILE_CACHE


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

        tg_update_in_db = await sync_to_async(TelegramUpdate.objects.create)(
            update_telegram_id=telegram_update.update_id,
            chat_telegram_id=telegram_update.effective_chat.id if telegram_update.effective_chat else None,
            arrival_timestamp_ms=arrival_timestamp_ms,
            payload=telegram_update_dict,
        )
        await sync_to_async(tg_update_in_db.save)()
        UPDATE_DB_MODELS_VOLATILE_CACHE[id(telegram_update)] = tg_update_in_db

        await application.process_update(telegram_update)

    asyncio.get_event_loop().create_task(_process_update())
    # TODO oleksandr: is it a good idea to respond with 200 OK before the update is processed ?
    return HttpResponse("OK")
