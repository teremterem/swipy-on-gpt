# pylint: disable=unused-argument,global-statement
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from telegram.ext.filters import User, TEXT

import gpt_completions
from gpt_completions_draft import SimpleGptCompletion, DialogGptCompletion
from swipy_config import TELEGRAM_TOKEN, ALLOWED_USERS

SIMPLE_GPT_COMP_T0: SimpleGptCompletion
SIMPLE_GPT_COMP_T1: SimpleGptCompletion
DIALOG_GPT_COMP_T0: DialogGptCompletion
DIALOG_GPT_COMP_T1: DialogGptCompletion

DIALOG_GPT: gpt_completions.DialogGptCompletionHistory | None = None


def init_gpt_completions() -> None:
    global SIMPLE_GPT_COMP_T0, SIMPLE_GPT_COMP_T1, DIALOG_GPT_COMP_T0, DIALOG_GPT_COMP_T1
    SIMPLE_GPT_COMP_T0 = SimpleGptCompletion(temperature=0)
    SIMPLE_GPT_COMP_T1 = SimpleGptCompletion(temperature=1)
    DIALOG_GPT_COMP_T0 = DialogGptCompletion(temperature=0)
    DIALOG_GPT_COMP_T1 = DialogGptCompletion(temperature=1)


init_gpt_completions()


# noinspection PyUnusedLocal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global DIALOG_GPT
    DIALOG_GPT = None

    await update.effective_chat.send_message(text="Hey Vsauce, Swipy here!")


# noinspection PyUnusedLocal
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global DIALOG_GPT
    if DIALOG_GPT is None:
        DIALOG_GPT = gpt_completions.DialogGptCompletionHistory(
            user_name=update.effective_user.username,
            bot_name="Swipy",
            temperature=1,
        )

    gpt_completion = DIALOG_GPT.new_user_utterance(update.effective_message.text)
    await update.effective_chat.send_message(text=gpt_completion.prompt, parse_mode=ParseMode.MARKDOWN)
    await gpt_completion.fulfil()
    await update.effective_chat.send_message(text=gpt_completion.completion, parse_mode=ParseMode.MARKDOWN)

    # await SIMPLE_GPT_COMP_T0.display_gpt_completion(update)
    # await asyncio.sleep(1)
    # await SIMPLE_GPT_COMP_T1.display_gpt_completion(update)
    # await asyncio.sleep(1)
    # await DIALOG_GPT_COMP_T0.display_gpt_completion(update)
    # await asyncio.sleep(1)
    # await DIALOG_GPT_COMP_T1.display_gpt_completion(update)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    allowed_users_filter = User(username=ALLOWED_USERS)

    application.add_handler(CommandHandler("start", start, filters=allowed_users_filter))
    application.add_handler(MessageHandler(TEXT, reply_to_user))

    application.run_polling()


if __name__ == "__main__":
    main()
