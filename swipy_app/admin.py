# pylint: disable=unused-argument,too-few-public-methods
from datetime import datetime
from functools import partial
from pprint import pformat

from asgiref.sync import async_to_sync
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions, action

from swipy_app.gpt_completions import GptCompletionSettings
from swipy_app.gpt_prompt_definitions import GEN_ALT_BUTTONS
from swipy_app.models import (
    TelegramUpdate,
    Utterance,
    GptCompletion,
    Conversation,
    SwipyUser,
    UtteranceConversation,
    SentMessage,
)
from swipy_app.swipy_bot import send_and_save_message


class SentMessageInline(admin.TabularInline):
    model = SentMessage
    ordering = ["sent_timestamp_ms"]
    fields = [
        "response_payload",
        "part_of_req_payload",
    ]
    can_delete = False
    show_change_link = True


class TelegramUpdateAdmin(admin.ModelAdmin):
    inlines = [SentMessageInline]
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
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', pformat(obj.payload, sort_dicts=False))

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class SentMessageAdmin(admin.ModelAdmin):
    ordering = ["-sent_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["sent_time", "pretty_response_payload", "pretty_part_of_req_payload", "swipy_user"]
    list_display_links = ["sent_time"]
    fields = [
        "swipy_user",
        "sent_time",
        "pretty_response_payload",
        "pretty_part_of_req_payload",
        "sent_timestamp_ms",
        "triggering_update",
    ]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Part of req. payload")
    def pretty_part_of_req_payload(self, obj):
        return format_html(
            '<pre style="white-space: pre-wrap">{}</pre>', pformat(obj.part_of_req_payload, sort_dicts=False)
        )

    @admin.display(description="Response payload")
    def pretty_response_payload(self, obj):
        return format_html(
            '<pre style="white-space: pre-wrap">{}</pre>', pformat(obj.response_payload, sort_dicts=False)
        )

    @admin.display(description="Arrival time")
    def sent_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.sent_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class GptCompletionAdmin(admin.ModelAdmin):
    ordering = ["-request_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "arrival_time", "completion", "alternative_to_utt_conv"]
    list_display_links = list_display
    fields = [
        "request_time",
        "arrival_time",
        "swipy_user",
        "prompt_pre",
        "completion_pre",
        "pretty_full_api_response",
        "estimated_prompt_token_number",
        "alternative_to_utt_conv",
        "prompt_name",
        "engine",
        "max_tokens",
        "temperature",
        "top_p",
        "frequency_penalty",
        "presence_penalty",
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

    @admin.display(description="Full API response")
    def pretty_full_api_response(self, obj):
        return format_html(
            '<pre style="white-space: pre-wrap">{}</pre>',
            pformat(obj.full_api_response, sort_dicts=False),
        )

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


class ConversationUtteranceInline(admin.TabularInline):
    model = UtteranceConversation
    ordering = ["utterance__arrival_timestamp_ms"]
    fields = ["utterance"]
    can_delete = False
    show_change_link = True


def generate_completion_alternatives(alt_list: list["GptCompletionSettings"], request, obj) -> None:
    obj.generate_alternatives(alt_list)


class ConversationAdmin(admin.ModelAdmin):
    inlines = [ConversationUtteranceInline]
    ordering = ["-last_update_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "title", "swipy_user", "last_update_time"]
    list_display_links = list_display
    fields = ["id", "title", "swipy_user", "last_update_time", "summary"]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Last update time")
    def last_update_time(self, conversation: Conversation) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(conversation.last_update_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class UtteranceConversationInline(admin.TabularInline):
    model = UtteranceConversation
    ordering = ["-conversation__last_update_timestamp_ms"]
    fields = ["conversation"]
    can_delete = False
    show_change_link = True


class AlternativeCompletionInline(admin.TabularInline):
    model = GptCompletion
    ordering = [
        "prompt_name",
        "temperature",
        "top_p",
        "request_timestamp_ms",
    ]
    fields = [
        "prompt_name",
        "temperature",
        # "top_p",
        "completion",
    ]
    can_delete = False
    show_change_link = True


class UtteranceAdmin(admin.ModelAdmin):
    inlines = [UtteranceConversationInline]
    ordering = ["-arrival_timestamp_ms"]
    list_filter = ["swipy_user"]
    # TODO oleksandr: find a way to display conversation_set in list view ?
    list_display = ["id", "arrival_time", "name", "text"]
    list_display_links = list_display
    fields = [
        "swipy_user",
        "telegram_message_id",
        "arrival_time",
        "name",
        "text",
        "is_bot",
        "triggering_update",
    ]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Arrival time")
    def arrival_time(self, utterance: Utterance) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(utterance.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class UtteranceConversationAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = [AlternativeCompletionInline]
    ordering = ["-utterance__arrival_timestamp_ms"]
    list_filter = ["utterance__swipy_user"]
    list_display = ["arrival_time", "utterance", "conversation"]
    list_display_links = list_display
    fields = [
        "chat_context",
        "utterance",
        "conversation",
        "gpt_completion",
        "arrival_time",
        "linked_time",
        "id",
    ]
    change_actions = [button_name for button_name, _ in GEN_ALT_BUTTONS]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Chat context")
    def chat_context(self, utt_conv_object: UtteranceConversation) -> str | None:
        if utt_conv_object.gpt_completion is None:
            return None
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', utt_conv_object.gpt_completion.prompt)

    @admin.display(description="Arrival time")
    def arrival_time(self, utt_conv_object: UtteranceConversation) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(utt_conv_object.utterance.arrival_timestamp_ms / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    @admin.display(description="Linked time")
    def linked_time(self, utt_conv_object: UtteranceConversation) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(utt_conv_object.linked_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


for (button_name, button_title), config_alternatives in GEN_ALT_BUTTONS.items():
    setattr(
        UtteranceConversationAdmin,
        button_name,
        action(label=button_title)(partial(generate_completion_alternatives, config_alternatives)),
    )


class ConversationInline(admin.TabularInline):
    # TODO oleksandr: make read-only
    model = Conversation
    ordering = ["-last_update_timestamp_ms"]
    fields = ["id", "title", "last_update_timestamp_ms"]
    readonly_fields = ["id", "title", "last_update_timestamp_ms"]
    can_delete = False
    show_change_link = True


class SwipyUserAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = [ConversationInline]
    ordering = ["full_name", "chat_telegram_id"]
    list_display = ["id", "full_name", "chat_telegram_id", "current_conversation"]
    list_display_links = ["id", "full_name", "chat_telegram_id"]
    fields = [
        "first_name",
        "full_name",
        "chat_telegram_id",
        "current_conversation",
        "language_code",
    ]
    readonly_fields = [
        "first_name",
        "full_name",
        "chat_telegram_id",
        # "current_conversation",
        # "language_code",
    ]
    change_actions = ["wake_up"]

    # turn language_code into a dropdown with two options
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "language_code":
            kwargs["widget"] = forms.Select(choices=[("en", "en"), ("uk", "uk")])
        return super().formfield_for_dbfield(db_field, **kwargs)

    def wake_up(self, request, obj):
        async_to_sync(send_and_save_message)(
            tg_update_in_db=None,
            swipy_user=obj,
            text=obj.get_lang().MSG_CHOOSE_LANGUAGE,
            reply_markup=[
                [obj.get_lang().BTN_ENGLISH],
                [obj.get_lang().BTN_UKRAINIAN],
            ],
        )

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False


admin.site.register(TelegramUpdate, TelegramUpdateAdmin)
admin.site.register(SentMessage, SentMessageAdmin)
admin.site.register(GptCompletion, GptCompletionAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(UtteranceConversation, UtteranceConversationAdmin)
admin.site.register(SwipyUser, SwipyUserAdmin)
