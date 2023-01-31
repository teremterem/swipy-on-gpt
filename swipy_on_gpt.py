# pylint: disable=unused-argument,global-statement
import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

from gpt_completions import DialogGptCompletionHistory
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

DIALOG_GPT_NO_PROMPT_T0 = DialogGptCompletionHistory(
    bot_name="Swipy",
    experiment_name="NO PROMPT",
    temperature=0,
)
DIALOG_GPT_NO_PROMPT_T1 = DialogGptCompletionHistory(
    bot_name="Swipy",
    experiment_name="NO PROMPT",
    temperature=1,
)


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    DIALOG_GPT_NO_PROMPT_T0.clear_history()
    DIALOG_GPT_NO_PROMPT_T1.clear_history()

    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


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
    await reply_with_gpt_completion(update, context, DIALOG_GPT_NO_PROMPT_T0)
    await reply_with_gpt_completion(update, context, DIALOG_GPT_NO_PROMPT_T1)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
