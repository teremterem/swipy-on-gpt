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
from swipy_app.swipy_l10n import SwipyL10n, LANGUAGES, DEFAULT_LANG
from swipy_app.swipy_utils import current_time_utc_ms

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}


def get_all_btn_set(lang: SwipyL10n) -> set[str]:
    all_btn_set = {
        lang.BTN_I_JUST_WANT_TO_CHAT,
        lang.BTN_SMTH_IS_BOTHERING_ME,
        lang.BTN_HELP_ME_FIGHT_PROCRAST,
        lang.BTN_SOMETHING_ELSE,
        lang.BTN_LANGUAGE,
        lang.BTN_MAIN_MENU,
        lang.BTN_EXPAND_ON_THIS,
        lang.BTN_THANKS,
        lang.BTN_NOT_HELPFUL,
        lang.BTN_PROCEED_WITH_SUBJECT,
        lang.BTN_ENGLISH,
        lang.BTN_UKRAINIAN,
    }
    return all_btn_set


async def reply_with_gpt_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    user_first_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    # TODO oleksandr: get language from db
    lang = LANGUAGES.get("en", DEFAULT_LANG)

    start_requested = update.effective_message.text == "/start"
    language_selected = update.effective_message.text in {lang.BTN_ENGLISH, lang.BTN_UKRAINIAN}
    any_reply_button_was_pressed = update.effective_message.text in get_all_btn_set(lang)
    expand_on_this_was_requested = update.effective_message.text == lang.BTN_EXPAND_ON_THIS
    main_menu_was_requested = update.effective_message.text == lang.BTN_MAIN_MENU
    thanks_was_requested = update.effective_message.text == lang.BTN_THANKS

    if expand_on_this_was_requested:
        gpt_completion_settings = NO_PROMPT_COMPLETION_CONFIG
    else:
        gpt_completion_settings = MAIN_COMPLETION_CONFIG

    if language_selected:
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
        [lang.BTN_I_JUST_WANT_TO_CHAT],
        [lang.BTN_SMTH_IS_BOTHERING_ME],
        [lang.BTN_HELP_ME_FIGHT_PROCRAST],
        [lang.BTN_SOMETHING_ELSE],
        [lang.BTN_LANGUAGE],
    ]

    if start_requested:
        gpt_completion_in_db = None

        response_msg = await update.effective_chat.send_message(
            text=lang.MSG_CHOOSE_LANGUAGE,
            reply_markup=ReplyKeyboardMarkup(
                [
                    [lang.BTN_ENGLISH],
                    [lang.BTN_UKRAINIAN],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    elif language_selected:
        gpt_completion_in_db = None

        response_msg = await update.effective_chat.send_message(
            text=lang.MSG_START_TEMPLATE.format(
                USER=user_first_name,
                BOT=gpt_completion_settings.prompt_settings.bot_name,
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
            text=lang.MSG_MAIN_MENU,
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
            buttons.append([lang.BTN_EXPAND_ON_THIS])
        elif expand_on_this_was_requested:
            buttons.append([lang.BTN_THANKS])
            buttons.append([lang.BTN_NOT_HELPFUL])
        elif thanks_was_requested:
            buttons.append([lang.BTN_PROCEED_WITH_SUBJECT])
        if not expand_on_this_was_requested:
            buttons.append([lang.BTN_MAIN_MENU])

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


# noinspection PyUnusedLocal
# TODO oleksandr: rename to telegram_application ?
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# TODO oleksandr: do you even need this kind of differentiation ?
application.add_handler(CommandHandler("start", reply_with_gpt_completion))
application.add_handler(MessageHandler(TEXT, reply_with_gpt_completion))

if __name__ == "__main__":
    application.run_polling()
