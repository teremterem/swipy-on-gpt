from django.db import models


class TelegramUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    arrival_timestamp_ms = models.BigIntegerField()
    telegram_update_id = models.BigIntegerField()
    payload = models.JSONField()

    def __str__(self):
        return f"TelegramUpdate(telegram_update_id={self.telegram_update_id})"
