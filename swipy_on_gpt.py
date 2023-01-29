import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.ext.filters import User

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):  # pylint: disable=unused-argument
    await update.effective_chat.send_message(text="I'm a bot, please talk to me!")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # make handlers work only for specific user_ids
    start_handler = CommandHandler("start", start, filters=User(username="@teremterem"))
    application.add_handler(start_handler)

    application.run_polling()
