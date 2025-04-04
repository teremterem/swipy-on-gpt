# Generated by Django 4.1.6 on 2023-02-19 10:55

from django.db import migrations


def populate_users(apps, schema_editor):
    from telegram import Update

    SwipyUser = apps.get_model("swipy_app", "SwipyUser")
    Utterance = apps.get_model("swipy_app", "Utterance")

    for chat_telegram_id in Utterance.objects.values_list("chat_telegram_id", flat=True).distinct():
        last_utterance = (
            Utterance.objects.filter(chat_telegram_id=chat_telegram_id).order_by("-arrival_timestamp_ms").first()
        )
        telegram_update = Update.de_json(last_utterance.triggering_update.payload, bot=None)
        user = SwipyUser.objects.create(
            chat_telegram_id=chat_telegram_id,
            first_name=telegram_update.effective_user.first_name,
            full_name=telegram_update.effective_user.full_name,
            current_conversation=last_utterance.conversation,
        )
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0009_swipyuser"),
    ]

    operations = [
        migrations.RunPython(populate_users, migrations.RunPython.noop),
    ]
