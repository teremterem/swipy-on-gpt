# pylint: disable=unused-argument
import asyncio
from datetime import datetime

from asgiref.sync import sync_to_async
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from swipy_bot.gpt_completions import DialogGptCompletionHistory
from swipy_bot.swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

BOT_NAME = "MoonRobot"
# TODO oleksandr: un-hardcode the user's name
FOLLOWUP_PROMPT = (
    f"Your name is {BOT_NAME} and the user's name is Oleksandr. Here is your dialog with Oleksandr. If Oleksandr "
    f"mentions any people, things, places, events etc. you don't know about (or if you don't know any details about "
    f"mentioned people, things, places, events etc. in relation to Oleksandr specifically) then follow up with "
    f"corresponding clarifying questions to Oleksandr.\n\n"
)

DIALOG = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="FOLLOWUP PROMPT",
    prompt_template=FOLLOWUP_PROMPT + "{}",
    temperature=0.0,
)

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE = {}


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    DIALOG.clear_history()
    # TODO oleksandr: all utterances (even hardcoded ones) should always be visible to GPT-3
    await update.effective_chat.send_message(text="MEMORY WIPED.")


async def reply_with_gpt_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, history: DialogGptCompletionHistory
) -> None:
    # pylint: disable=import-outside-toplevel
    # TODO oleksandr: when to import this ?
    from swipy_app.models import Utterance

    user_name = update.effective_user.first_name
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
    arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    utterance_in_db = await sync_to_async(Utterance.objects.create)(
        arrival_timestamp_ms=arrival_timestamp_ms,
        chat_telegram_id=update.effective_chat.id,
        telegram_message_id=update.effective_message.message_id,
        triggering_update=tg_update_in_db,
        name=user_name,
        text=update.effective_message.text,
        is_bot=False,
    )
    await sync_to_async(utterance_in_db.save)()

    gpt_completion = history.new_user_utterance(user_name, update.effective_message.text)

    keep_typing = True

    async def _keep_typing_task():
        for _ in range(10):
            if not keep_typing:
                break
            await update.effective_chat.send_chat_action(ChatAction.TYPING)
            await asyncio.sleep(10)

    await asyncio.sleep(1)
    asyncio.get_event_loop().create_task(_keep_typing_task())

    # await update.effective_chat.send_message(
    #     text=f"{str(history).upper()}\n\n" f"{gpt_completion.prompt}",
    #     parse_mode=ParseMode.MARKDOWN,
    # )
    await gpt_completion.fulfil(tg_update_in_db)
    keep_typing = False

    # add a button to the message
    response_msg = await update.effective_chat.send_message(
        text=gpt_completion.completion,
        # parse_mode=ParseMode.MARKDOWN,  # TODO oleksandr: do I need markdown for anything ?
        # reply_markup=InlineKeyboardMarkup(
        #     [
        #         [
        #             InlineKeyboardButton(text="👍", callback_data="like"),
        #             InlineKeyboardButton(text="👎", callback_data="dislike"),
        #         ]
        #     ],
        # ),
    )

    # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
    arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    utterance_in_db = await sync_to_async(Utterance.objects.create)(
        arrival_timestamp_ms=arrival_timestamp_ms,
        chat_telegram_id=response_msg.chat.id,
        telegram_message_id=response_msg.message_id,
        triggering_update=tg_update_in_db,
        name=gpt_completion.bot_name,
        text=response_msg.text,
        is_bot=True,
        gpt_completion=gpt_completion.gpt_completion_in_db,
    )
    await sync_to_async(utterance_in_db.save)()


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_gpt_completion(update, context, DIALOG)


application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
allowed_users_filter = User(username=ALLOWED_USERS)

application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
# TODO oleksandr: add /ping command
application.add_handler(MessageHandler(TEXT & allowed_users_filter, reply_to_user))

if __name__ == "__main__":
    application.run_polling()
