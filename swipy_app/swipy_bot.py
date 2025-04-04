# pylint: disable=unused-argument
import asyncio
from typing import Sequence, Union

from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Message
from telegram._utils.types import ReplyMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT

from swipy_app.gpt_prompt_definitions import MAIN_COMPLETION_CONFIG, NO_PROMPT_COMPLETION_CONFIG
from swipy_app.models import Utterance, TelegramUpdate, UtteranceConversation, SentMessage, SwipyUser
from swipy_app.swipy_config import TELEGRAM_TOKEN
from swipy_app.swipy_l10n import SwipyL10n
from swipy_app.swipy_utils import current_time_utc_ms

# TODO oleksandr: is this a dirty hack ? use this instead ?
#  https://stackoverflow.com/questions/30596484/python-asyncio-context
UPDATE_DB_MODELS_VOLATILE_CACHE: dict[int, TelegramUpdate] = {}

CMD_START = "/start"


def get_all_btn_set(lang: SwipyL10n) -> set[str]:
    all_btn_set = {
        lang.BTN_I_JUST_WANT_TO_CHAT,
        lang.BTN_SMTH_IS_BOTHERING_ME,
        lang.BTN_HELP_ME_FIGHT_PROCRAST,
        lang.BTN_SOMETHING_ELSE,
        lang.BTN_CHANGE_LANGUAGE,
        lang.BTN_MAIN_MENU,
        lang.BTN_EXPAND_ON_THIS,
        lang.BTN_THANKS,
        lang.BTN_NOT_HELPFUL,
        lang.BTN_PROCEED_WITH_SUBJECT,
        lang.BTN_ENGLISH,
        lang.BTN_UKRAINIAN,
        CMD_START,
    }
    return all_btn_set


def get_main_menu(lang: SwipyL10n) -> list[list[str]]:
    menu = [
        [lang.BTN_I_JUST_WANT_TO_CHAT],
        [lang.BTN_SMTH_IS_BOTHERING_ME],
        [lang.BTN_HELP_ME_FIGHT_PROCRAST],
        [lang.BTN_SOMETHING_ELSE],
        [lang.BTN_CHANGE_LANGUAGE],
    ]
    return menu


async def reboot_old_conversation(reply_to_message: Message, tg_update_in_db: TelegramUpdate) -> None:
    replied_to_utterance = await sync_to_async(
        Utterance.objects.filter(telegram_message_id=reply_to_message.message_id).first
    )()
    if not replied_to_utterance:
        return
    replied_to_utt_conv_object = await sync_to_async(
        # take the oldest link
        UtteranceConversation.objects.filter(utterance=replied_to_utterance)
        .order_by("linked_timestamp_ms")
        .first
    )()
    if not replied_to_utt_conv_object:
        return

    # start a new conversation
    await tg_update_in_db.swipy_user.detach_current_conversation()
    conversation = await tg_update_in_db.swipy_user.get_current_conversation()

    new_link_timestamp_ms = current_time_utc_ms()

    utt_conv_objects = await sync_to_async(list)(
        UtteranceConversation.objects.filter(conversation_id=replied_to_utt_conv_object.conversation_id)
        .select_related("utterance")
        .order_by("utterance__arrival_timestamp_ms")
    )
    for utt_conv_object in utt_conv_objects:
        await UtteranceConversation.objects.acreate(
            conversation=conversation,  # create a link with the new conversation
            utterance_id=utt_conv_object.utterance_id,
            linked_timestamp_ms=new_link_timestamp_ms,
        )
        if utt_conv_object.utterance == replied_to_utterance:
            # stop at the replied to utterance
            break


async def reply_with_gpt_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    user_first_name = update.effective_user.first_name  # TODO oleksandr: update db user info upon every tg update ?
    tg_update_in_db = UPDATE_DB_MODELS_VOLATILE_CACHE.pop(id(update))

    if update.effective_message.reply_to_message:
        await reboot_old_conversation(update.effective_message.reply_to_message, tg_update_in_db)

    lang = tg_update_in_db.swipy_user.get_lang()

    any_reply_button_was_pressed = update.effective_message.text in get_all_btn_set(lang)
    language_change_requested = update.effective_message.text in {CMD_START, lang.BTN_CHANGE_LANGUAGE}
    language_selected = update.effective_message.text in {lang.BTN_ENGLISH, lang.BTN_UKRAINIAN}
    expand_on_this_was_requested = update.effective_message.text == lang.BTN_EXPAND_ON_THIS
    main_menu_was_requested = update.effective_message.text == lang.BTN_MAIN_MENU
    thanks_was_requested = update.effective_message.text == lang.BTN_THANKS
    help_fight_procrast_was_requested = update.effective_message.text == lang.BTN_HELP_ME_FIGHT_PROCRAST

    if expand_on_this_was_requested:
        gpt_completion_settings = NO_PROMPT_COMPLETION_CONFIG
    else:
        gpt_completion_settings = MAIN_COMPLETION_CONFIG

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
        conversation_id=await tg_update_in_db.swipy_user.get_current_conversation_id(),
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

    if language_change_requested:
        gpt_completion_in_db = None

        response_msg = await send_and_save_message(
            tg_update_in_db=tg_update_in_db,
            text=lang.MSG_CHOOSE_LANGUAGE,
            reply_markup=[
                [lang.BTN_ENGLISH],
                [lang.BTN_UKRAINIAN],
            ],
        )

    elif language_selected or main_menu_was_requested:
        gpt_completion_in_db = None

        if language_selected:
            # update language
            if update.effective_message.text == lang.BTN_ENGLISH:
                tg_update_in_db.swipy_user.language_code = "en"
            elif update.effective_message.text == lang.BTN_UKRAINIAN:
                tg_update_in_db.swipy_user.language_code = "uk"
            await sync_to_async(tg_update_in_db.swipy_user.save)(update_fields=["language_code"])

        # start a new conversation
        await tg_update_in_db.swipy_user.detach_current_conversation()

        lang = tg_update_in_db.swipy_user.get_lang()

        response_msg = await send_and_save_message(
            tg_update_in_db=tg_update_in_db,
            text=lang.MSG_START_TEMPLATE.format(
                USER=user_first_name,
                BOT=gpt_completion_settings.prompt_settings.bot_name,
            ),
            reply_markup=get_main_menu(lang),
        )

    elif help_fight_procrast_was_requested:
        gpt_completion_in_db = None

        asyncio.get_event_loop().create_task(_keep_typing_task())
        await asyncio.sleep(1)

        keep_typing = False

        response_msg = await send_and_save_message(
            tg_update_in_db=tg_update_in_db,
            text=lang.MSG_HELP_FIGHT_PROCRAST,
            reply_markup=[
                [lang.BTN_MAIN_MENU],
            ],
        )

    else:
        if not any_reply_button_was_pressed:
            await asyncio.sleep(1)  # TODO oleksandr: start processing in parallel maybe ?
        asyncio.get_event_loop().create_task(_keep_typing_task())

        gpt_completion = await gpt_completion_settings.fulfil_completion(
            swipy_user=tg_update_in_db.swipy_user,
            conversation_id=await tg_update_in_db.swipy_user.get_current_conversation_id(),
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

        response_msg = await send_and_save_message(
            tg_update_in_db=tg_update_in_db,
            text=response_text,
            reply_markup=buttons,
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
        conversation_id=await tg_update_in_db.swipy_user.get_current_conversation_id(),
        gpt_completion=gpt_completion_in_db,
    )
    if gpt_completion_in_db:
        gpt_completion_in_db.alternative_to_utt_conv = utt_conv_object
        await sync_to_async(gpt_completion_in_db.save)(update_fields=["alternative_to_utt_conv"])
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user.current_conversation (maybe not here)
    # TODO oleksandr: update last_update_timestamp_ms in swipy_user too ? (maybe not here)


async def send_and_save_message(
    tg_update_in_db: TelegramUpdate | None,
    text: str,
    reply_markup: ReplyMarkup | Sequence[Sequence[Union[str, KeyboardButton]]] | None = None,
    resize_keyboard: bool = True,
    one_time_keyboard: bool = True,
    swipy_user: SwipyUser | None = None,
    chat_id: Union[int, str] | None = None,
):
    # pylint: disable=too-many-arguments
    if not swipy_user:
        swipy_user = tg_update_in_db.swipy_user
    if not chat_id:
        chat_id = swipy_user.chat_telegram_id
    if reply_markup:
        if not isinstance(reply_markup, (ReplyKeyboardMarkup, ReplyKeyboardRemove)):
            reply_markup = ReplyKeyboardMarkup(
                keyboard=reply_markup,
                resize_keyboard=resize_keyboard,
                one_time_keyboard=one_time_keyboard,
            )

    response_msg = await application.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )
    await SentMessage.objects.acreate(
        triggering_update=tg_update_in_db,
        swipy_user=swipy_user,
        sent_timestamp_ms=current_time_utc_ms(),
        response_payload=response_msg.to_dict(),
        part_of_req_payload=reply_markup.to_dict() if reply_markup else None,
    )
    return response_msg


# noinspection PyUnusedLocal
# TODO oleksandr: rename to telegram_application ?
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# TODO oleksandr: do you even need this kind of differentiation ?
application.add_handler(CommandHandler("start", reply_with_gpt_completion))
application.add_handler(MessageHandler(TEXT, reply_with_gpt_completion))

if __name__ == "__main__":
    application.run_polling()
