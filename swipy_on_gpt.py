# pylint: disable=unused-argument,global-statement
import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import DialogGptCompletionHistory
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

BOT_NAME = "Swipy"
# TODO oleksandr: unhardcode the names
CURIOS_PROMPT = (
    "Swipy is a chatbot that uses GPT-3 to answer questions from a user by the name Oleksandr. "
    "Swipy is genuinely curious and wants to learn more about Oleksandr. For that reason it asks Oleksandr followup "
    "questions to clarify every detail that is not immediately clear to Swipy in whatever Oleksandr is telling "
    "Swipy. Below is a conversation between Swipy and Oleksandr.\n\n"
)

NO_PROMPT_T0 = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="NO PROMPT",
    temperature=0,
)
NO_PROMPT_T1 = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="NO PROMPT",
    temperature=1,
)
CURIOUS_PROMPT_T0 = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="CURIOUS PROMPT",
    prompt_template=CURIOS_PROMPT + "{}",
    temperature=0,
)
CURIOUS_PROMPT_T1 = DialogGptCompletionHistory(
    bot_name=BOT_NAME,
    experiment_name="CURIOUS PROMPT",
    prompt_template=CURIOS_PROMPT + "{}",
    temperature=1,
)


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    NO_PROMPT_T0.clear_history()
    NO_PROMPT_T1.clear_history()

    # TODO oleksandr: all utterances (even hardcoded ones) should always be visible to GPT-3
    await update.effective_chat.send_message(text=f"Hey Vsauce, {BOT_NAME} here!")


async def reply_with_gpt_completion(
    update: Update, context: ContextTypes.DEFAULT_TYPE, history: DialogGptCompletionHistory
) -> None:
    gpt_completion = history.new_user_utterance(update.effective_user.first_name, update.effective_message.text)
    await asyncio.sleep(0.1)
    await update.effective_chat.send_message(
        text=f"{str(history).upper()}\n\n" f"{gpt_completion.prompt}",
        parse_mode=ParseMode.MARKDOWN,
    )
    await gpt_completion.fulfil()
    await update.effective_chat.send_message(text=gpt_completion.completion, parse_mode=ParseMode.MARKDOWN)


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_with_gpt_completion(update, context, NO_PROMPT_T0)
    await reply_with_gpt_completion(update, context, NO_PROMPT_T1)
    await reply_with_gpt_completion(update, context, CURIOUS_PROMPT_T0)
    await reply_with_gpt_completion(update, context, CURIOUS_PROMPT_T1)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
