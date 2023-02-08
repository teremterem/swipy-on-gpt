# pylint: disable=unused-argument
from datetime import datetime
from pprint import pformat

from django.contrib import admin
from django.utils.html import format_html

from swipy_app.models import TelegramUpdate


class TelegramUpdateAdmin(admin.ModelAdmin):
    ordering = ["-arrival_timestamp_ms"]
    list_filter = ["telegram_chat_id"]
    list_display = ["id", "arrival_time", "pretty_payload", "telegram_chat_id"]
    list_display_links = list_display
    fields = ["telegram_chat_id", "telegram_update_id", "arrival_time", "pretty_payload", "arrival_timestamp_ms"]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Payload")
    def pretty_payload(self, obj):
        return format_html("<pre>{}</pre>", pformat(obj.payload))

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


admin.site.register(TelegramUpdate, TelegramUpdateAdmin)
