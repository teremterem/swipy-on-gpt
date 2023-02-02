from django.http import HttpResponse, HttpRequest


def index(request: HttpRequest) -> HttpResponse:  # pylint: disable=unused-argument
    return HttpResponse("Hello, world!")
