from django.db import models


class TelegramUpdate(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    chat_telegram_id = models.BigIntegerField(null=True)
    update_telegram_id = models.BigIntegerField()

    payload = models.JSONField()


class Utterance(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    chat_telegram_id = models.BigIntegerField()
    telegram_message_id = models.BigIntegerField()
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)

    name = models.TextField()
    text = models.TextField()
    is_bot = models.BooleanField()
