# Generated by Django 4.1.6 on 2023-02-19 11:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0015_auto_20230219_1149"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gptcompletion",
            name="chat_telegram_id",
        ),
        migrations.RemoveField(
            model_name="telegramupdate",
            name="chat_telegram_id",
        ),
        migrations.RemoveField(
            model_name="utterance",
            name="chat_telegram_id",
        ),
    ]
