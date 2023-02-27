# pylint: disable=too-few-public-methods
from datetime import datetime

from asgiref.sync import sync_to_async
from django.db import models


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
    alternative_to_utterance = models.ForeignKey("Utterance", on_delete=models.CASCADE, null=True)

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
        return f"{self.id} - {self.title}"


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
                # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
                last_update_timestamp_ms=int(datetime.utcnow().timestamp() * 1000),
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
