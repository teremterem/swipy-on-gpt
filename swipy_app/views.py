import logging

from django.http import HttpResponse, HttpRequest


async def index(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    logging.getLogger().debug("debug Aloha, world!")
    return HttpResponse("Hello, world!")
