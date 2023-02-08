from django.db import models


class TelegramUpdate(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    telegram_chat_id = models.BigIntegerField(null=True)
    telegram_update_id = models.BigIntegerField()
    payload = models.JSONField()
