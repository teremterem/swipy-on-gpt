# Generated by Django 4.1.6 on 2023-02-17 21:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0004_alter_gptcompletion_arrival_timestamp_ms_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="utterance",
            name="is_end_of_conv",
            field=models.BooleanField(default=False),
        ),
    ]
