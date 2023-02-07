# pylint: disable=unused-argument
import asyncio

from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import DialogGptCompletionHistory
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

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


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    DIALOG.clear_history()
    # TODO oleksandr: all utterances (even hardcoded ones) should always be visible to GPT-3
    await update.effective_chat.send_message(text="MEMORY WIPED.")


async def reply_with_gpt_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, history: DialogGptCompletionHistory
) -> None:
    gpt_completion = history.new_user_utterance(update.effective_user.first_name, update.effective_message.text)

    keep_typing = True

    async def keep_typing_task():
        while keep_typing:
            await update.effective_chat.send_chat_action(ChatAction.TYPING)
            await asyncio.sleep(10)

    await asyncio.sleep(1)
    asyncio.get_event_loop().create_task(keep_typing_task())

    # await update.effective_chat.send_message(
    #     text=f"{str(history).upper()}\n\n" f"{gpt_completion.prompt}",
    #     parse_mode=ParseMode.MARKDOWN,
    # )
    await gpt_completion.fulfil()
    keep_typing = False

    # add a button to the message
    await update.effective_chat.send_message(
        text=gpt_completion.completion,
        parse_mode=ParseMode.MARKDOWN,
        # reply_markup=InlineKeyboardMarkup(
        #     [
        #         [
        #             InlineKeyboardButton(text="👍", callback_data="like"),
        #             InlineKeyboardButton(text="👎", callback_data="dislike"),
        #         ]
        #     ],
        # ),
    )


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
