# Generated by Django 4.1.7 on 2023-03-12 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0035_gptcompletion_estimated_prompt_token_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="SentMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sent_timestamp_ms", models.BigIntegerField()),
                ("part_of_req_payload", models.JSONField(blank=True, null=True)),
                ("response_payload", models.JSONField()),
                (
                    "swipy_user",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="swipy_app.swipyuser"
                    ),
                ),
                (
                    "triggering_update",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="swipy_app.telegramupdate"
                    ),
                ),
            ],
        ),
    ]
