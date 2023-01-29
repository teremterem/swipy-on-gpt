import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.ext.filters import User

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USERS = os.environ["ALLOWED_USERS"].split(",")
print(ALLOWED_USERS)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):  # pylint: disable=unused-argument
    await update.effective_chat.send_message(text="I'm a bot, please talk to me!")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    start_handler = CommandHandler("start", start, filters=allowed_users_filter)
    application.add_handler(start_handler)

    application.run_polling()
