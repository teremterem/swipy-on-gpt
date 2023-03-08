# pylint: disable=unused-argument,too-few-public-methods
from datetime import datetime
from functools import partial
from pprint import pformat

from django.contrib import admin
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions, action

from swipy_app.gpt_completions import GptCompletionSettings
from swipy_app.gpt_prompt_definitions import GEN_ALT_BUTTONS
from swipy_app.models import TelegramUpdate, Utterance, GptCompletion, Conversation, SwipyUser, UtteranceConversation


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
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', pformat(obj.payload, sort_dicts=False))

    @admin.display(description="Arrival time")
    def arrival_time(self, obj):
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(obj.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class GptCompletionAdmin(admin.ModelAdmin):
    ordering = ["-request_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "arrival_time", "completion", "alternative_to_utterance"]
    list_display_links = list_display
    fields = [
        "request_time",
        "arrival_time",
        "swipy_user",
        "prompt_pre",
        "completion_pre",
        "pretty_full_api_response",
        "alternative_to_utterance",
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


class ConversationAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = [ConversationUtteranceInline]
    ordering = ["-last_update_timestamp_ms"]
    list_filter = ["swipy_user"]
    list_display = ["id", "title", "swipy_user", "last_update_time"]
    list_display_links = list_display
    fields = ["id", "title", "swipy_user", "last_update_time", "summary"]
    change_actions = [button_name for button_name, _ in GEN_ALT_BUTTONS]

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


for (button_name, button_title), config_alternatives in GEN_ALT_BUTTONS.items():
    setattr(
        ConversationAdmin,
        button_name,
        action(label=button_title)(partial(generate_completion_alternatives, config_alternatives)),
    )


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


class UtteranceAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = [UtteranceConversationInline, AlternativeCompletionInline]
    ordering = ["-arrival_timestamp_ms"]
    list_filter = ["swipy_user"]
    # TODO oleksandr: find a way to display conversation_set in list view
    list_display = ["id", "arrival_time", "name", "text"]
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
        "chat_context",
    ]
    change_actions = [button_name for button_name, _ in GEN_ALT_BUTTONS]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Chat context")
    def chat_context(self, utterance: Utterance) -> str | None:
        if utterance.gpt_completion is None:
            return None
        return format_html('<pre style="white-space: pre-wrap">{}</pre>', utterance.gpt_completion.prompt)

    @admin.display(description="Arrival time")
    def arrival_time(self, utterance: Utterance) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(utterance.arrival_timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


class UtteranceConversationAdmin(admin.ModelAdmin):  # (DjangoObjectActions, admin.ModelAdmin):
    # inlines = [UtteranceConversationInline, AlternativeCompletionInline]
    ordering = ["-utterance__arrival_timestamp_ms"]
    list_filter = ["utterance__swipy_user"]
    list_display = ["id", "arrival_time", "conversation", "utterance"]
    list_display_links = list_display
    fields = [
        "chat_context",
        "utterance",
        "conversation",
    ]

    # change_actions = [button_name for button_name, _ in GEN_ALT_BUTTONS]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Chat context")
    def chat_context(self, utt_conv_object: UtteranceConversation) -> str | None:
        if utt_conv_object.utterance.gpt_completion is None:
            return None
        return format_html(
            '<pre style="white-space: pre-wrap">{}</pre>', utt_conv_object.utterance.gpt_completion.prompt
        )

    @admin.display(description="Arrival time")
    def arrival_time(self, utt_conv_object: UtteranceConversation) -> str:
        # TODO oleksandr: get rid of duplicate code
        return datetime.fromtimestamp(utt_conv_object.utterance.arrival_timestamp_ms / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )


for (button_name, button_title), config_alternatives in GEN_ALT_BUTTONS.items():
    setattr(
        UtteranceAdmin,
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
    ]
    readonly_fields = [
        "first_name",
        "full_name",
        "chat_telegram_id",
        # "current_conversation",
    ]
    change_actions = [button_name for button_name, _ in GEN_ALT_BUTTONS]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False


for (button_name, button_title), config_alternatives in GEN_ALT_BUTTONS.items():
    setattr(
        SwipyUserAdmin,
        button_name,
        action(label=button_title)(partial(generate_completion_alternatives, config_alternatives)),
    )

admin.site.register(TelegramUpdate, TelegramUpdateAdmin)
admin.site.register(GptCompletion, GptCompletionAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Utterance, UtteranceAdmin)
admin.site.register(UtteranceConversation, UtteranceConversationAdmin)
admin.site.register(SwipyUser, SwipyUserAdmin)
