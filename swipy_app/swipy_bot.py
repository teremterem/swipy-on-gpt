# pylint: disable=unused-argument
import asyncio

from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT

from swipy_app.gpt_prompt_definitions import MAIN_COMPLETION_CONFIG, NO_PROMPT_COMPLETION_CONFIG
from swipy_app.models import Utterance, TelegramUpdate, UtteranceConversation
from swipy_app.swipy_config import TELEGRAM_TOKEN
from swipy_app.swipy_utils import current_time_utc_ms

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}

BTN_I_JUST_WANT_TO_CHAT = "I just wanna chat 😊"
BTN_SMTH_IS_BOTHERING_ME = "Something’s bothering me 😔"
BTN_HELP_ME_FIGHT_PROCRAST = "Help me fight procrastination ✅"
BTN_SOMETHING_ELSE = "Something else 🤔"
BTN_MAIN_MENU = "Main menu 🏠"
BTN_EXPAND_ON_THIS = "Expand on this 📚"
BTN_THANKS = "Thanks 🌟"
BTN_NOT_USEFUL = "Not useful 💔"
BTN_PROCEED_WITH_SUBJECT = "Let's proceed with this subject 📚"

ALL_BTN_SET = {
    BTN_I_JUST_WANT_TO_CHAT,
    BTN_SMTH_IS_BOTHERING_ME,
    BTN_HELP_ME_FIGHT_PROCRAST,
    BTN_SOMETHING_ELSE,
    BTN_MAIN_MENU,
    BTN_EXPAND_ON_THIS,
    BTN_THANKS,
    BTN_NOT_USEFUL,
    BTN_PROCEED_WITH_SUBJECT,
}


async def reply_with_gpt_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # pylint: disable=too-many-locals,too-many-statements
    user_requested_new_conv = update.effective_message.text == "/start"
    any_reply_button_was_pressed = update.effective_message.text in ALL_BTN_SET
    expand_on_this_was_requested = update.effective_message.text == BTN_EXPAND_ON_THIS
    main_menu_was_requested = update.effective_message.text == BTN_MAIN_MENU
    thanks_was_requested = update.effective_message.text == BTN_THANKS

    if expand_on_this_was_requested:
        gpt_completion_settings = NO_PROMPT_COMPLETION_CONFIG
    else:
        gpt_completion_settings = MAIN_COMPLETION_CONFIG

    user_first_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

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

    main_menu = [
        [BTN_I_JUST_WANT_TO_CHAT],
        [BTN_SMTH_IS_BOTHERING_ME],
        [BTN_HELP_ME_FIGHT_PROCRAST],
        [BTN_SOMETHING_ELSE],
    ]

    if user_requested_new_conv:
        gpt_completion_in_db = None

        response_msg = await update.effective_chat.send_message(
            text=(
                f"Hi {user_first_name}! My name is {gpt_completion_settings.prompt_settings.bot_name}🤖\n"
                f"\n"
                f"How can I help you? 😊"
            ),
            reply_markup=ReplyKeyboardMarkup(
                main_menu,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    elif main_menu_was_requested:
        gpt_completion_in_db = None

        response_msg = await update.effective_chat.send_message(
            text="Sure, what would you like?",
            reply_markup=ReplyKeyboardMarkup(
                main_menu,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    else:
        if not any_reply_button_was_pressed:
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

        buttons = []
        if not any_reply_button_was_pressed:
            buttons.append([BTN_EXPAND_ON_THIS])
        elif expand_on_this_was_requested:
            buttons.append([BTN_THANKS])
            buttons.append([BTN_NOT_USEFUL])
        elif thanks_was_requested:
            buttons.append([BTN_PROCEED_WITH_SUBJECT])
        buttons.append([BTN_MAIN_MENU])

        response_msg = await update.effective_chat.send_message(
            text=response_text,
            reply_markup=ReplyKeyboardMarkup(
                buttons,
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

    # if expand_on_this_was_requested:
    #     # TODO TODO TODO TODO TODO
    #     # TODO TODO TODO TODO TODO oleksandr: resolve code duplication
    #     # TODO TODO TODO TODO TODO
    #
    #     keep_typing = True
    #
    #     asyncio.get_event_loop().create_task(_keep_typing_task())
    #
    #     gpt_completion_settings = MAIN_COMPLETION_CONFIG
    #
    #     gpt_completion = await gpt_completion_settings.fulfil_completion(
    #         swipy_user=tg_update_in_db.swipy_user,
    #         conversation_id=conversation_id,
    #         tg_update_in_db=tg_update_in_db,
    #     )
    #     response_text = gpt_completion.completion.strip()  # TODO oleksandr: minor: is stripping necessary ?
    #     gpt_completion_in_db = gpt_completion.gpt_completion_in_db
    #
    #     keep_typing = False
    #
    #     response_msg = await update.effective_chat.send_message(
    #         text=response_text,
    #         reply_markup=ReplyKeyboardMarkup(
    #             [[BTN_MAIN_MENU]],
    #             resize_keyboard=True,
    #             one_time_keyboard=True,
    #         ),
    #     )
    #
    #     utterance = await Utterance.objects.acreate(
    #         arrival_timestamp_ms=current_time_utc_ms(),
    #         swipy_user=tg_update_in_db.swipy_user,
    #         telegram_message_id=response_msg.message_id,  # TODO oleksandr: store complete message json in db ?
    #         triggering_update=tg_update_in_db,
    #         name=gpt_completion_settings.prompt_settings.bot_name,
    #         text=response_msg.text,
    #         is_bot=True,
    #     )
    #     utt_conv_object = await UtteranceConversation.objects.acreate(
    #         linked_timestamp_ms=utterance.arrival_timestamp_ms,
    #         utterance=utterance,
    #         conversation_id=conversation_id,
    #         gpt_completion=gpt_completion_in_db,
    #     )
    #     if gpt_completion_in_db:
    #         gpt_completion_in_db.alternative_to_utt_conv = utt_conv_object
    #         await sync_to_async(gpt_completion_in_db.save)(update_fields=["alternative_to_utt_conv"])
    #     # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation (maybe not here)
    #     # TODO oleksandr: update last_update_timestamp_ms in swipy_user too ? (maybe not here)


# noinspection PyUnusedLocal
# TODO oleksandr: rename to telegram_application ?
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# TODO oleksandr: do you even need this kind of differentiation ?
application.add_handler(CommandHandler("start", reply_with_gpt_completion))
application.add_handler(MessageHandler(TEXT, reply_with_gpt_completion))

if __name__ == "__main__":
    application.run_polling()
