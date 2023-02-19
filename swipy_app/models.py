# pylint: disable=too-few-public-methods
from django.db import models


class TelegramUpdate(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    chat_telegram_id = models.BigIntegerField(null=True)
    update_telegram_id = models.BigIntegerField()

    payload = models.JSONField()


class GptCompletion(models.Model):
    request_timestamp_ms = models.BigIntegerField()
    arrival_timestamp_ms = models.BigIntegerField(null=True)
    # TODO oleksandr: processing time ?
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)
    chat_telegram_id = models.BigIntegerField(null=True)

    prompt = models.TextField(null=True, blank=True)
    completion = models.TextField(null=True, blank=True)
    temperature = models.FloatField(null=True)


# TODO oleksandr: create user object


class Conversation(models.Model):
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE, null=True)
    last_update_timestamp_ms = models.BigIntegerField()


class Utterance(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    chat_telegram_id = models.BigIntegerField()
    telegram_message_id = models.BigIntegerField()
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)

    name = models.TextField()
    text = models.TextField()
    is_bot = models.BooleanField()

    # TODO oleksandr: get rid of this field when conversations are fully implemented
    is_end_of_conv = models.BooleanField(default=False)

    gpt_completion = models.ForeignKey(GptCompletion, on_delete=models.CASCADE, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)


class SwipyUser(models.Model):
    chat_telegram_id = models.BigIntegerField()
    first_name = models.TextField()
    full_name = models.TextField()
    current_conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.full_name} - {self.chat_telegram_id}"
