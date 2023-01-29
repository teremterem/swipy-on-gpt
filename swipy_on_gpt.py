# pylint: disable=unused-argument
from contextlib import nullcontext
from unittest.mock import patch

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_caller import perform_gpt_completion
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS, MOCK_GPT


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = await perform_gpt_completion(update.effective_message.text)
    await update.effective_chat.send_message(text=answer, parse_mode="Markdown")


def main() -> None:
    if MOCK_GPT:
        mock_gpt_context = patch(
            "gpt_caller.perform_gpt_completion", return_value="hErE gOeS gPt ReSpOnSe (iT's a mOCK!)"
        )
    else:
        mock_gpt_context = nullcontext()

    with mock_gpt_context:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        allowed_users_filter = User(username=ALLOWED_USERS)

        application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
        application.add_handler(MessageHandler(TEXT, reply_to_user))

        application.run_polling()


if __name__ == "__main__":
    main()
