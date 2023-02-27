# pylint: disable=unused-argument
import asyncio
from datetime import datetime

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT

from swipy_app.models import Utterance, TelegramUpdate
from swipy_bot.gpt_completions import DialogGptCompletionFactory
from swipy_bot.swipy_config import TELEGRAM_TOKEN, BOT_NAME

FOLLOWUP_PROMPT = (
    "Your name is {BOT} and the user's name is {USER}. Here is your dialog with {USER}. If {USER} "
    "mentions any people, things, places, events etc. you don't know about (or if you don't know details about "
    "mentioned people, things, places, events etc. in relation to {USER} specifically) then follow up with "
    "corresponding clarifying questions to {USER}.\n\n{DIALOG}"
)
DIALOG = DialogGptCompletionFactory(
    bot_name=BOT_NAME,
    prompt_template=FOLLOWUP_PROMPT,
)

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}


async def reply_with_gpt_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, completion_factory: DialogGptCompletionFactory
) -> None:
    user_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    if update.effective_message.text == "/start":
        # start a new conversation
        await tg_update_in_db.swipy_user.detach_current_conversation()

    # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
    arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    await Utterance.objects.acreate(
        arrival_timestamp_ms=arrival_timestamp_ms,
        swipy_user=tg_update_in_db.swipy_user,
        conversation=await tg_update_in_db.swipy_user.get_current_conversation(),
        telegram_message_id=update.effective_message.message_id,
        triggering_update=tg_update_in_db,
        name=user_name,
        text=update.effective_message.text,
        is_bot=False,
    )
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation

    gpt_completion = completion_factory.new_completion(tg_update_in_db.swipy_user)

    keep_typing = True

    async def _keep_typing_task():
        for _ in range(10):
            if not keep_typing:
                break
            await update.effective_chat.send_chat_action(ChatAction.TYPING)
            await asyncio.sleep(10)

    await asyncio.sleep(1)
    asyncio.get_event_loop().create_task(_keep_typing_task())

    await gpt_completion.fulfil(tg_update_in_db)
    keep_typing = False

    response_msg = await update.effective_chat.send_message(
        text=gpt_completion.completion.strip(),  # TODO oleksandr: minor: is stripping necessary ?
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
    await Utterance.objects.acreate(
        arrival_timestamp_ms=arrival_timestamp_ms,
        swipy_user=tg_update_in_db.swipy_user,
        conversation=await tg_update_in_db.swipy_user.get_current_conversation(),
        telegram_message_id=response_msg.message_id,
        triggering_update=tg_update_in_db,
        name=gpt_completion.settings.bot_name,
        text=response_msg.text,
        is_bot=True,
        gpt_completion=gpt_completion.gpt_completion_in_db,
    )
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_gpt_completion(update, context, DIALOG)


# TODO oleksandr: rename to telegram_application ?
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

application.add_handler(CommandHandler("start", reply_to_user))
application.add_handler(MessageHandler(TEXT, reply_to_user))

if __name__ == "__main__":
    application.run_polling()
