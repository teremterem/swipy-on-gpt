# Generated by Django 4.1.7 on 2023-03-07 20:00

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0026_auto_20230307_1939"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="utterance",
            name="conversation_obsolete",
        ),
    ]
