# Generated by Django 4.1.6 on 2023-02-27 06:49
import traceback

from asgiref.sync import async_to_sync
from django.db import migrations


def summarize_conversations(apps, schema_editor):
    # TODO oleksandr: this might be a bad idea - implementation might change over time
    # TODO oleksandr: replace with ChatGptCompletion
    from swipy_app.gpt_completions import DialogGptCompletionFactory
    from swipy_app.swipy_config import BOT_NAME

    Conversation = apps.get_model("swipy_app", "Conversation")

    summarizer = DialogGptCompletionFactory(
        bot_name=BOT_NAME,
        prompt_template=(
            "Your name is {BOT} and the user's name is {USER}. Here is your dialog with {USER}. Summarize what can be "
            "learned from this dialog using a bulleted list of short sentences.\n\n{DIALOG}\n\n# SUMMARY"
        ),
        append_bot_name_at_the_end=False,
        max_tokens=1024,
        temperature=0.0,
    )
    titler = DialogGptCompletionFactory(
        bot_name=BOT_NAME,
        prompt_template=(
            "Your name is {BOT} and the user's name is {USER}. Here is your dialog with {USER}. Give this dialog a "
            "short and concise title.\n\n{DIALOG}\n\n# TITLE:"
        ),
        append_bot_name_at_the_end=False,
        temperature=0.0,
    )

    for conversation in Conversation.objects.all():
        if not conversation.summary:
            try:
                summary_completion = summarizer.new_completion(conversation.swipy_user)
                async_to_sync(summary_completion.fulfil)(
                    conversation_id=conversation.pk,
                    tg_update_in_db=None,
                )
                conversation.summary = summary_completion.completion.strip()
                conversation.save(update_fields=["summary"])
            except Exception as e:
                print(f"Failed to summarize conversation {conversation.pk}: {e}")
                traceback.print_exc()

        if not conversation.title:
            try:
                title_completion = titler.new_completion(conversation.swipy_user)
                async_to_sync(title_completion.fulfil)(
                    conversation_id=conversation.pk,
                    tg_update_in_db=None,
                )
                conversation.title = title_completion.completion.strip()
                conversation.save(update_fields=["title"])
            except Exception as e:
                print(f"Failed to title conversation {conversation.pk}")
                traceback.print_exc()


class Migration(migrations.Migration):
    dependencies = [
        ("swipy_app", "0018_conversation_summary_conversation_title"),
    ]

    operations = [
        migrations.RunPython(summarize_conversations, migrations.RunPython.noop),
    ]
