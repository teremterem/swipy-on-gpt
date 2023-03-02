from swipy_app.gpt_completions import GptPromptSettings, DialogGptCompletionFactory, GptCompletionSettings
from swipy_app.swipy_config import BOT_NAME

ASK_EVERYTHING_PROMPT = GptPromptSettings(
    prompt_name="ask-everything-0.3",
    prompt_template=(
        "Your name is {BOT} and the user's name is {USER}. Below is your conversation with {USER}. If {USER} "
        "mentions any people, things, places, events etc. you don't know about (or if you don't know details about "
        "mentioned people, things, places, events etc. in relation to {USER} specifically) then follow up with "
        "corresponding clarifying questions to {USER}.\n"
        "\n"
        "---\n"
        "\n"
        "{DIALOG}"
    ),
)
DIALOG = DialogGptCompletionFactory(
    settings=GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_PROMPT,
    ),
    bot_name=BOT_NAME,
)
ALTERNATIVE_DIALOGS = [
    DIALOG,  # temperature=1.0 (default)
    DialogGptCompletionFactory(
        settings=GptCompletionSettings(
            prompt_settings=ASK_EVERYTHING_PROMPT,
            temperature=0.7,
        ),
        bot_name=BOT_NAME,
    ),
    DialogGptCompletionFactory(
        settings=GptCompletionSettings(
            prompt_settings=ASK_EVERYTHING_PROMPT,
            temperature=0.3,
        ),
        bot_name=BOT_NAME,
    ),
    DialogGptCompletionFactory(
        settings=GptCompletionSettings(
            prompt_settings=ASK_EVERYTHING_PROMPT,
            temperature=0.0,
        ),
        bot_name=BOT_NAME,
    ),
]
