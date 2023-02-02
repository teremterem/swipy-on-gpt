from django.urls import path

from swipy_config import TELEGRAM_TOKEN
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(f"{TELEGRAM_TOKEN}/", views.telegram_webhook, name="telegram_webhook"),
]
