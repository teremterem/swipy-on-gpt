import json
from datetime import datetime
from functools import wraps

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
    arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

    telegram_update_dict = json.loads(request.body)
    telegram_update = Update.de_json(telegram_update_dict, application.bot)

    TelegramUpdate.objects.create(
        telegram_update_id=telegram_update.update_id,
        arrival_timestamp_ms=arrival_timestamp_ms,
        payload=telegram_update_dict,
    ).save()

    await application.process_update(telegram_update)
    return HttpResponse("OK")  # TODO oleksandr: first, respond with 200, then process the update asynchronously ?
