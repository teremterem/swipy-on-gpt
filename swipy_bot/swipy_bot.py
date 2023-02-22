# pylint: disable=unused-argument
import asyncio
from datetime import datetime

from asgiref.sync import sync_to_async
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT

from swipy_app.models import Utterance, TelegramUpdate
from swipy_bot.gpt_completions import DialogGptCompletionHistory
from swipy_bot.swipy_config import TELEGRAM_TOKEN

BOT_NAME = "Swipy"  # TODO oleksandr: read from getMe()

FOLLOWUP_PROMPT = (
    f"Your name is {BOT_NAME} and the user's name is {{USER}}. Here is your dialog with {{USER}}. If {{USER}} "
    f"mentions any people, things, places, events etc. you don't know about (or if you don't know any details about "
    f"mentioned people, things, places, events etc. in relation to {{USER}} specifically) then follow up with "
    f"corresponding clarifying questions to {{USER}}.\n\n{{DIALOG}}"
)
DIALOG = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="FOLLOWUP PROMPT",
    prompt_template=FOLLOWUP_PROMPT,
    temperature=0.0,
)

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}


async def reply_with_gpt_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, history: DialogGptCompletionHistory
) -> None:
    user_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    if update.effective_message.text == "/start":
        # start a new conversation
        tg_update_in_db.swipy_user.current_conversation = None
        await sync_to_async(tg_update_in_db.swipy_user.save)(update_fields=["current_conversation"])

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

    gpt_completion = history.new_user_utterance(user_name)

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
        name=gpt_completion.bot_name,
        text=response_msg.text,
        is_bot=True,
        gpt_completion=gpt_completion.gpt_completion_in_db,
    )
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_gpt_completion(update, context, DIALOG)


application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# TODO oleksandr: get rid of this completely:
#  allowed_users_filter = User(username=ALLOWED_USERS)

application.add_handler(CommandHandler("start", reply_to_user))  # TODO oleksandr: filters=allowed_users_filter
application.add_handler(MessageHandler(TEXT, reply_to_user))  # TODO oleksandr: TEXT & allowed_users_filter

if __name__ == "__main__":
    application.run_polling()
