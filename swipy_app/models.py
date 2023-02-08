from django.db import models


class TelegramUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    arrival_timestamp_ms = models.BigIntegerField()
    telegram_chat_id = models.BigIntegerField(null=True)
    telegram_update_id = models.BigIntegerField()
    payload = models.JSONField()
