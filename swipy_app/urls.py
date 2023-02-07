from django.urls import path

from swipy_config import TELEGRAM_TOKEN
from . import views

urlpatterns = [
    path("h3a11h/", views.health_check, name="health_check"),
    path(f"{TELEGRAM_TOKEN}/", views.telegram_webhook, name="telegram_webhook"),
]
