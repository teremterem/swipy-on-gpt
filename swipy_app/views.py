import json
from functools import wraps

from django.http import HttpResponse, HttpRequest
from telegram import Update

from swipy_bot import application


async def index(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    # TODO oleksandr: get rid of this view for security reasons ?
    return HttpResponse("Hello, cruel world!")


async def health_check(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    return HttpResponse("Hello, world!")


def csrf_exempt_async(view_func):
    async def wrapped_view(*args, **kwargs):
        return await view_func(*args, **kwargs)

    wrapped_view.csrf_exempt = True
    return wraps(view_func)(wrapped_view)


@csrf_exempt_async
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    telegram_update = Update.de_json(json.loads(request.body), application.bot)
    await application.process_update(telegram_update)
    return HttpResponse("OK")
