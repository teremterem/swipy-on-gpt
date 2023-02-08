# Generated by Django 4.1.6 on 2023-02-08 16:02

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TelegramUpdate",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("arrival_timestamp_ms", models.BigIntegerField()),
                ("telegram_update_id", models.BigIntegerField()),
                ("payload", models.JSONField()),
            ],
        ),
    ]
