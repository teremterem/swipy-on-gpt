# pylint: disable=unused-argument,too-few-public-methods
from datetime import datetime
from pprint import pformat

from django.contrib import admin
from django.utils.html import format_html

from swipy_app.models import TelegramUpdate, Utterance, GptCompletion, Conversation, SwipyUser


class TelegramUpdateAdmin(admin.ModelAdmin):
    ordering = ["-arrival_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "arrival_time", "pretty_payload", "swipy_user"]
    list_display_links = ["id", "arrival_time"]
    fields = ["swipy_user", "update_telegram_id", "arrival_time", "pretty_payload", "arrival_timestamp_ms"]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Payload")
    def pretty_payload(self, obj):
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', pformat(obj.payload))

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class GptCompletionAdmin(admin.ModelAdmin):
    ordering = ["-request_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "request_time", "arrival_time", "completion"]
    list_display_links = list_display
    fields = [
        "request_time",
        "arrival_time",
        "prompt_pre",
        "completion_pre",
        "temperature",
        "triggering_update",
        "request_timestamp_ms",
        "arrival_timestamp_ms",
    ]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Prompt")
    def prompt_pre(self, obj):
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', obj.prompt)

    @admin.display(description="Completion")
    def completion_pre(self, obj):
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', obj.completion)

    @admin.display(description="Request time")
    def request_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.request_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        if obj.arrival_timestamp_ms is None:
            return "N/A"
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class UtteranceInline(admin.TabularInline):
    # TODO oleksandr: make read-only
    model = Utterance
    ordering = ["arrival_timestamp_ms"]
    fields = ["name", "text"]
    can_delete = False
    can_add = False
    can_edit = False
    show_change_link = True


class ConversationAdmin(admin.ModelAdmin):
    inlines = [UtteranceInline]
    ordering = ["-last_update_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "swipy_user", "last_update_time"]
    list_display_links = list_display
    fields = ["id", "swipy_user", "last_update_time"]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Last update time")
    def last_update_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.last_update_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class UtteranceAdmin(admin.ModelAdmin):
    ordering = ["-arrival_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "arrival_time", "name", "text", "conversation"]
    list_display_links = list_display
    fields = [
        "swipy_user",
        "telegram_message_id",
        "arrival_time",
        "name",
        "text",
        "is_bot",
        "gpt_completion",
        "triggering_update",
        "conversation",
    ]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class ConversationInline(admin.TabularInline):
    # TODO oleksandr: make read-only
    model = Conversation
    ordering = ["-last_update_timestamp_ms"]
    fields = ["id", "last_update_timestamp_ms"]
    readonly_fields = ["id", "last_update_timestamp_ms"]
    can_delete = False
    can_add = False
    can_edit = False
    show_change_link = True


class SwipyUserAdmin(admin.ModelAdmin):
    inlines = [ConversationInline]
    ordering = ["full_name", "chat_telegram_id"]
    list_display = ["id", "full_name", "chat_telegram_id", "current_conversation"]
    list_display_links = ["id", "full_name", "chat_telegram_id"]
    fields = [
        "first_name",
        "full_name",
        "chat_telegram_id",
        "current_conversation",
    ]
    readonly_fields = [
        "first_name",
        "full_name",
        "chat_telegram_id",
        # "current_conversation",
    ]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False


admin.site.register(TelegramUpdate, TelegramUpdateAdmin)
admin.site.register(GptCompletion, GptCompletionAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(SwipyUser, SwipyUserAdmin)
