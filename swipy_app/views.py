from django.http import HttpResponse, HttpRequest


async def index(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    return HttpResponse("Hello, world!")
