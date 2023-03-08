# pylint: disable=unused-argument
import asyncio

from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT

from swipy_app.gpt_completions import GptCompletionSettings
from swipy_app.gpt_prompt_definitions import MAIN_COMPLETION_CONFIG
from swipy_app.models import Utterance, TelegramUpdate, UtteranceConversation
from swipy_app.swipy_config import TELEGRAM_TOKEN
from swipy_app.swipy_utils import current_time_utc_ms

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}


async def reply_with_gpt_completion(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    gpt_completion_settings: GptCompletionSettings,
) -> None:
    user_first_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    user_requested_new_conv = update.effective_message.text == "/start"
    if user_requested_new_conv:
        # start a new conversation
        await tg_update_in_db.swipy_user.detach_current_conversation()

    conversation_id = await tg_update_in_db.swipy_user.get_current_conversation_id()

    utterance = await Utterance.objects.acreate(
        arrival_timestamp_ms=current_time_utc_ms(),
        swipy_user=tg_update_in_db.swipy_user,
        telegram_message_id=update.effective_message.message_id,
        triggering_update=tg_update_in_db,
        name=user_first_name,
        text=update.effective_message.text,
        is_bot=False,
    )
    await UtteranceConversation.objects.acreate(
        linked_timestamp_ms=utterance.arrival_timestamp_ms,
        utterance=utterance,
        conversation_id=conversation_id,
    )
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user too ?

    keep_typing = True

    async def _keep_typing_task():
        for _ in range(10):
            if not keep_typing:
                break
            await update.effective_chat.send_chat_action(ChatAction.TYPING)
            await asyncio.sleep(10)

    if user_requested_new_conv:
        gpt_completion_in_db = None

        response_msg = await update.effective_chat.send_message(
            text=(
                f"Hi {user_first_name}! My name is {gpt_completion_settings.prompt_settings.bot_name}🤖\n"
                f"\n"
                f"How can I help you? 😊"
            ),
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["I just wanna chat 😊"],
                    ["Something’s bothering me 😔"],
                    ["Help me fight procrastination ✅"],
                    ["Something else 🤔"],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    else:
        await asyncio.sleep(1)  # TODO oleksandr: start processing in parallel maybe ?
        asyncio.get_event_loop().create_task(_keep_typing_task())

        gpt_completion = await gpt_completion_settings.fulfil_completion(
            swipy_user=tg_update_in_db.swipy_user,
            conversation_id=conversation_id,
            tg_update_in_db=tg_update_in_db,
        )
        response_text = gpt_completion.completion.strip()  # TODO oleksandr: minor: is stripping necessary ?
        gpt_completion_in_db = gpt_completion.gpt_completion_in_db

        keep_typing = False
        response_msg = await update.effective_chat.send_message(
            text=response_text,
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Expand on this 📚"],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    utterance = await Utterance.objects.acreate(
        arrival_timestamp_ms=current_time_utc_ms(),
        swipy_user=tg_update_in_db.swipy_user,
        telegram_message_id=response_msg.message_id,  # TODO oleksandr: store complete message json in db ?
        triggering_update=tg_update_in_db,
        name=gpt_completion_settings.prompt_settings.bot_name,
        text=response_msg.text,
        is_bot=True,
    )
    utt_conv_object = await UtteranceConversation.objects.acreate(
        linked_timestamp_ms=utterance.arrival_timestamp_ms,
        utterance=utterance,
        conversation_id=conversation_id,
        gpt_completion=gpt_completion_in_db,
    )
    if gpt_completion_in_db:
        gpt_completion_in_db.alternative_to_utt_conv = utt_conv_object
        await sync_to_async(gpt_completion_in_db.save)(update_fields=["alternative_to_utt_conv"])
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation (maybe not here)
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user too ? (maybe not here)


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_gpt_completion(update, context, MAIN_COMPLETION_CONFIG)


# TODO oleksandr: rename to telegram_application ?
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# TODO oleksandr: do you even need this kind of differentiation ?
application.add_handler(CommandHandler("start", reply_to_user))
application.add_handler(MessageHandler(TEXT, reply_to_user))

if __name__ == "__main__":
    application.run_polling()
