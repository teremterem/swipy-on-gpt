# Generated by Django 4.1.7 on 2023-03-07 19:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0024_rename_conversation_utterance_conversation_obsolete"),
    ]

    operations = [
        migrations.AlterField(
            model_name="utterance",
            name="conversation_obsolete",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="utterance_set_obsolete",
                to="swipy_app.conversation",
            ),
        ),
        migrations.CreateModel(
            name="UtteranceConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("linked_timestamp_ms", models.BigIntegerField()),
                (
                    "conversation",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="swipy_app.conversation"),
                ),
                (
                    "utterance",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="swipy_app.utterance"),
                ),
            ],
            options={
                "unique_together": {("utterance", "conversation")},
            },
        ),
        migrations.AddField(
            model_name="utterance",
            name="conversation_set",
            field=models.ManyToManyField(through="swipy_app.UtteranceConversation", to="swipy_app.conversation"),
        ),
    ]
