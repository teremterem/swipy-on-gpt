# Generated by Django 4.1.6 on 2023-02-26 19:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0016_remove_gptcompletion_chat_telegram_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gptcompletion",
            name="engine",
            field=models.TextField(default="text-davinci-003"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="gptcompletion",
            name="frequency_penalty",
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="gptcompletion",
            name="max_tokens",
            field=models.IntegerField(default=512),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="gptcompletion",
            name="presence_penalty",
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="gptcompletion",
            name="top_p",
            field=models.FloatField(default=1.0),
            preserve_default=False,
        ),
    ]
