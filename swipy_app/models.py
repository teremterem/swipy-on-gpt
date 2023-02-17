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


class Utterance(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    chat_telegram_id = models.BigIntegerField()
    telegram_message_id = models.BigIntegerField()
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)

    name = models.TextField()
    text = models.TextField()
    is_bot = models.BooleanField()
    is_end_of_conv = models.BooleanField(default=False)
    gpt_completion = models.ForeignKey(GptCompletion, on_delete=models.CASCADE, null=True)
