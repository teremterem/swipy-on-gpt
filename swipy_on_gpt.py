# pylint: disable=unused-argument
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import SimpleGptCompletion, DialogGptCompletion
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

SIMPLE_GPT_COMP_T0: SimpleGptCompletion
SIMPLE_GPT_COMP_T1: SimpleGptCompletion
DIALOG_GPT_COMP_T0: DialogGptCompletion
DIALOG_GPT_COMP_T1: DialogGptCompletion


def init_gpt_completions() -> None:
    # pylint: disable=global-statement
    global SIMPLE_GPT_COMP_T0, SIMPLE_GPT_COMP_T1, DIALOG_GPT_COMP_T0, DIALOG_GPT_COMP_T1
    SIMPLE_GPT_COMP_T0 = SimpleGptCompletion(temperature=0)
    SIMPLE_GPT_COMP_T1 = SimpleGptCompletion(temperature=1)
    DIALOG_GPT_COMP_T0 = DialogGptCompletion(temperature=0)
    DIALOG_GPT_COMP_T1 = DialogGptCompletion(temperature=1)


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
    await asyncio.sleep(1)
    await DIALOG_GPT_COMP_T0.display_gpt_completion(update)
    await asyncio.sleep(1)
    await DIALOG_GPT_COMP_T1.display_gpt_completion(update)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
