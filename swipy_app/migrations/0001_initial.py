# Generated by Django 4.1.6 on 2023-02-08 23:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TelegramUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("arrival_timestamp_ms", models.BigIntegerField()),
                ("chat_telegram_id", models.BigIntegerField(null=True)),
                ("update_telegram_id", models.BigIntegerField()),
                ("payload", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="Utterance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("arrival_timestamp_ms", models.BigIntegerField()),
                ("chat_telegram_id", models.BigIntegerField()),
                ("telegram_message_id", models.BigIntegerField()),
                ("name", models.TextField()),
                ("text", models.TextField()),
                ("is_bot", models.BooleanField()),
                (
                    "triggering_update",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="swipy_app.telegramupdate"
                    ),
                ),
            ],
        ),
    ]
