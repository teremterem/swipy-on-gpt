# pylint: disable=unused-argument
import logging
import os

import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USERS = os.environ["ALLOWED_USERS"].split(",")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


async def perform_gpt_completion(prompt: str) -> str:
    # TODO oleksandr: replace with "text-davinci-003"
    gpt_response = await openai.Completion.acreate(prompt=prompt, engine="text-ada-001")
    assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
    return prompt + gpt_response.choices[0].text


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = await perform_gpt_completion(update.effective_message.text)
    await update.effective_chat.send_message(text=answer, parse_mode="Markdown")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()
