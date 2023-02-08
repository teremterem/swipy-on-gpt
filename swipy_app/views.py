import json
from datetime import datetime
from functools import wraps

from asgiref.sync import sync_to_async
from django.http import HttpResponse, HttpRequest
from telegram import Update

from swipy_app.models import TelegramUpdate
from swipy_bot import application


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

    telegram_update_dict = json.loads(request.body)
    telegram_update = Update.de_json(telegram_update_dict, application.bot)

    tg_update_in_db = await sync_to_async(TelegramUpdate.objects.create)(
        update_telegram_id=telegram_update.update_id,
        chat_telegram_id=telegram_update.effective_chat.id if telegram_update.effective_chat else None,
        arrival_timestamp_ms=arrival_timestamp_ms,
        payload=telegram_update_dict,
    )
    await sync_to_async(tg_update_in_db.save)()
    telegram_update._database_model = tg_update_in_db  # pylint: disable=protected-access

    await application.process_update(telegram_update)
    return HttpResponse("OK")  # TODO oleksandr: first, respond with 200, then process the update asynchronously ?
