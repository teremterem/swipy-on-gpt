# pylint: disable=unused-argument,global-statement
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import DialogGptCompletionHistory
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

DIALOG_GPT_T1: DialogGptCompletionHistory | None = None


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global DIALOG_GPT_T1
    DIALOG_GPT_T1 = None

    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global DIALOG_GPT_T1
    if DIALOG_GPT_T1 is None:
        DIALOG_GPT_T1 = DialogGptCompletionHistory(
            user_name=update.effective_user.first_name,
            bot_name="Swipy",
            temperature=1,
        )

    gpt_completion = DIALOG_GPT_T1.new_user_utterance(update.effective_message.text)
    # await update.effective_chat.send_message(text=gpt_completion.prompt, parse_mode=ParseMode.MARKDOWN)
    await gpt_completion.fulfil()
    await update.effective_chat.send_message(text=gpt_completion.completion, parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
