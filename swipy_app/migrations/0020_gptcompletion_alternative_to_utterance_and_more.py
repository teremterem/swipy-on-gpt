# Generated by Django 4.1.6 on 2023-02-27 20:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0019_auto_20230227_0649"),
    ]

    operations = [
        migrations.AddField(
            model_name="gptcompletion",
            name="alternative_to_utterance",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="swipy_app.utterance"),
        ),
        migrations.AddField(
            model_name="gptcompletion",
            name="prompt_name",
            field=models.TextField(default="ask-everything-0.1-or-0.2"),
            preserve_default=False,
        ),
    ]
