# pylint: disable=too-few-public-methods
from django.db import models


class TelegramUpdate(models.Model):
    arrival_timestamp_ms = models.BigIntegerField()
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)
    update_telegram_id = models.BigIntegerField()

    payload = models.JSONField()


class GptCompletion(models.Model):
    request_timestamp_ms = models.BigIntegerField()
    arrival_timestamp_ms = models.BigIntegerField(null=True)
    # TODO oleksandr: processing time ?
    triggering_update = models.ForeignKey(TelegramUpdate, on_delete=models.CASCADE, null=True)
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)

    prompt = models.TextField(null=True, blank=True)
    completion = models.TextField(null=True, blank=True)
    temperature = models.FloatField(null=True)


class Conversation(models.Model):
    swipy_user = models.ForeignKey("SwipyUser", on_delete=models.CASCADE)
    last_update_timestamp_ms = models.BigIntegerField()


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

    # TODO oleksandr: get rid of this field when conversations are fully implemented
    is_end_of_conv = models.BooleanField(default=False)

    gpt_completion = models.ForeignKey(GptCompletion, on_delete=models.CASCADE, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)


class SwipyUser(models.Model):
    # TODO oleksandr: shouldn't it be user_telegram_id plus chat_telegram_id ?
    chat_telegram_id = models.BigIntegerField(db_index=True)
    first_name = models.TextField()
    full_name = models.TextField()
    current_conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.full_name)
