# Generated by Django 4.1.6 on 2023-02-14 19:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0003_gptcompletion_temperature"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gptcompletion",
            name="arrival_timestamp_ms",
            field=models.BigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="gptcompletion",
            name="completion",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="gptcompletion",
            name="prompt",
            field=models.TextField(blank=True, null=True),
        ),
    ]
