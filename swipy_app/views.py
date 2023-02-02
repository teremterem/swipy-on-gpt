import json

from asgiref.sync import sync_to_async, async_to_sync
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from telegram import Update

from swipy_bot import application
from swipy_config import TELEGRAM_TOKEN


async def index(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    # TODO oleksandr: unhardcode the webhook url and ideally manage to call it once during the app startup
    webhook_url = f"https://0e93-94-131-248-62.ngrok.io/swipy/{TELEGRAM_TOKEN}/"
    print(webhook_url)
    print(await application.bot.set_webhook(webhook_url))  # TODO oleksandr: get rid of print
    return HttpResponse("Hello, world!")


@sync_to_async
@csrf_exempt  # TODO oleksandr: fix for async ? https://code.djangoproject.com/ticket/31949
@async_to_sync
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    # parse request body json into dict
    await application.initialize()
    telegram_update = Update.de_json(json.loads(request.body), application.bot)
    await application.process_update(telegram_update)
    # set telegram webhook url
    # respond with 200 OK
    return HttpResponse("OK")
