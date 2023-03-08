# Generated by Django 4.1.7 on 2023-03-08 15:37

from django.db import migrations


def move_gpt_completion_from_utterance_to_utt_conv(apps, schema_editor):
    UtteranceConversation = apps.get_model("swipy_app", "UtteranceConversation")
    for utt_conv_object in UtteranceConversation.objects.all():
        if utt_conv_object.utterance.gpt_completion:
            utt_conv_object.gpt_completion = utt_conv_object.utterance.gpt_completion
            utt_conv_object.save(update_fields=["gpt_completion"])


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0031_utteranceconversation_gpt_completion"),
    ]

    operations = [
        migrations.RunPython(move_gpt_completion_from_utterance_to_utt_conv, migrations.RunPython.noop),
    ]
