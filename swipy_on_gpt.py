# pylint: disable=unused-argument
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USERS = os.environ["ALLOWED_USERS"].split(",")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(text="I'm a bot, please talk to me!")


# noinspection PyUnusedLocal
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(text="GPT-3 ?")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, gpt))

    application.run_polling()
