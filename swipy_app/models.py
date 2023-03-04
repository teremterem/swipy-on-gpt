# pylint: disable=too-few-public-methods
import typing
from collections import namedtuple

from asgiref.sync import sync_to_async, async_to_sync
from django.db import models

from swipy_app.swipy_utils import current_time_utc_ms

if typing.TYPE_CHECKING:
    from swipy_app.gpt_completions import GptCompletionSettings


class TelegramUpdate(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE, null=True)
    update_telegram_id = models.BigIntegerField()

    payload = models.JSONField()


class GptCompletion(models.Model):
    request_timestamp_ms = models.BigIntegerField()
    arrival_timestamp_ms = models.BigIntegerField(null=True)
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)
    alternative_to_utterance = models.ForeignKey(
        "Utterance",
        on_delete=models.CASCADE,
        null=True,
        related_name="alternative_completion_set",
    )

    prompt = models.TextField(null=True, blank=True)
    completion = models.TextField(null=True, blank=True)

    prompt_name = models.TextField(null=True, blank=True)
    engine = models.TextField()
    max_tokens = models.IntegerField()
    temperature = models.FloatField(null=True)
    top_p = models.FloatField()
    frequency_penalty = models.FloatField()
    presence_penalty = models.FloatField()


class Conversation(models.Model):
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)
    last_update_timestamp_ms = models.BigIntegerField()

    title = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.pk} - {self.title}"

    def generate_alternatives(self, alternative_completion_factories: list["GptCompletionSettings"]) -> None:
        for utterance in self.utterance_set.all():
            if utterance.is_bot:
                utterance.generate_alternatives(alternative_completion_factories)


class Utterance(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["swipy_user", "arrival_timestamp_ms"]),
        ]

    arrival_timestamp_ms = models.BigIntegerField()
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)
    telegram_message_id = models.BigIntegerField()
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)

    name = models.TextField()
    text = models.TextField()
    is_bot = models.BooleanField()

    gpt_completion = models.ForeignKey(GptCompletion, on_delete=models.CASCADE, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)

    def generate_alternatives(self, completion_config_alternatives: list["GptCompletionSettings"]) -> None:
        existing_alternatives = {}
        for existing_alternative in self.alternative_completion_set.all():
            key = _CompletionSettingsTuple(
                prompt_name=existing_alternative.prompt_name,
                engine=existing_alternative.engine,
                max_tokens=existing_alternative.max_tokens,
                temperature=existing_alternative.temperature,
                top_p=existing_alternative.top_p,
                frequency_penalty=existing_alternative.frequency_penalty,
                presence_penalty=existing_alternative.presence_penalty,
            )
            existing_alternatives[key] = existing_alternatives.get(key, 0) + 1

        for completion_config in completion_config_alternatives:
            key = _CompletionSettingsTuple(
                prompt_name=completion_config.prompt_settings.prompt_name,
                engine=completion_config.engine,
                max_tokens=completion_config.max_tokens,
                temperature=completion_config.temperature,
                top_p=completion_config.top_p,
                frequency_penalty=completion_config.frequency_penalty,
                presence_penalty=completion_config.presence_penalty,
            )
            missing_count = 2 if completion_config.temperature else 1
            missing_count -= existing_alternatives.get(key, 0)
            for _ in range(missing_count):
                completion = async_to_sync(completion_config.fulfil_completion)(
                    swipy_user=self.swipy_user,
                    conversation_id=self.conversation_id,
                    stop_before_utterance=self,
                )
                completion.gpt_completion_in_db.alternative_to_utterance = self
                completion.gpt_completion_in_db.save(update_fields=["alternative_to_utterance"])


class SwipyUser(models.Model):
    # TODO oleksandr: shouldn't it be user_telegram_id plus chat_telegram_id ?
    chat_telegram_id = models.BigIntegerField(unique=True)
    first_name = models.TextField(null=True, blank=True)
    full_name = models.TextField(null=True, blank=True)
    current_conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.full_name)

    async def get_current_conversation(self) -> Conversation:
        """
        Returns the current conversation for this user, creating it if it doesn't exist yet.
        """
        if not self.current_conversation:
            self.current_conversation = await Conversation.objects.acreate(
                swipy_user=self,
                last_update_timestamp_ms=current_time_utc_ms(),
            )
            await sync_to_async(self.save)(update_fields=["current_conversation"])
        return self.current_conversation

    async def get_current_conversation_id(self) -> int:
        """
        Returns the id of the current conversation for this user, creating the conversations if it doesn't exist yet.
        """
        if not self.current_conversation_id:
            return (await self.get_current_conversation()).pk
        return self.current_conversation_id

    async def detach_current_conversation(self) -> None:
        """
        Detaches the current conversation from this user.
        """
        self.current_conversation = None
        await sync_to_async(self.save)(update_fields=["current_conversation"])
        # self.current_conversation_id is assigned with None automatically, no need to do it explicitly

    def generate_alternatives(self, completion_config_alternatives: list["GptCompletionSettings"]) -> None:
        for conversation in self.conversation_set.all():
            conversation.generate_alternatives(completion_config_alternatives)


_CompletionSettingsTuple = namedtuple(
    "CompletionSettings",
    [
        "prompt_name",
        "engine",
        "max_tokens",
        "temperature",
        "top_p",
        "frequency_penalty",
        "presence_penalty",
    ],
)
