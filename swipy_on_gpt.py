# pylint: disable=unused-argument
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import SimpleCompletionBase
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

SIMPLE_GPT_COMP_T0: SimpleCompletionBase
SIMPLE_GPT_COMP_T1: SimpleCompletionBase


def init_gpt_completions() -> None:
    global SIMPLE_GPT_COMP_T0, SIMPLE_GPT_COMP_T1  # pylint: disable=global-statement
    SIMPLE_GPT_COMP_T0 = SimpleCompletionBase(temperature=0)
    SIMPLE_GPT_COMP_T1 = SimpleCompletionBase(temperature=1)


init_gpt_completions()


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_gpt_completions()
    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await SIMPLE_GPT_COMP_T0.display_gpt_completion(update)
    await asyncio.sleep(1)
    await SIMPLE_GPT_COMP_T1.display_gpt_completion(update)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
