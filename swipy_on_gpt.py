# pylint: disable=unused-argument
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS, MOCK_GPT


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = await display_gpt_completion(update.effective_message.text)
    await update.effective_chat.send_message(text=answer, parse_mode="Markdown")


async def display_gpt_completion(prompt: str) -> str:
    completion = await request_gpt_completion(prompt)
    return prompt + completion


async def request_gpt_completion(prompt: str) -> str:
    if MOCK_GPT:
        return " hErE gOeS gPt ReSpOnSe (iT's a mOCK!)"

    # TODO oleksandr: replace with "text-davinci-003"
    gpt_response = await openai.Completion.acreate(prompt=prompt, engine="text-ada-001")
    assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"

    return gpt_response.choices[0].text


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
