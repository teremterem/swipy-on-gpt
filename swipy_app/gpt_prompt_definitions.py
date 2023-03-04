from swipy_app.gpt_completions import GptPromptSettings, GptCompletionSettings, TextDialogGptCompletion
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
    bot_name=BOT_NAME,
)
MAIN_COMPLETION_CONFIG = GptCompletionSettings(
    completion_class=TextDialogGptCompletion,
    prompt_settings=ASK_EVERYTHING_PROMPT,
)
COMPLETION_CONFIG_ALTERNATIVES = [
    MAIN_COMPLETION_CONFIG,  # temperature=1.0 (default)
    GptCompletionSettings(
        completion_class=TextDialogGptCompletion,
        prompt_settings=ASK_EVERYTHING_PROMPT,
        temperature=0.5,
    ),
    GptCompletionSettings(
        completion_class=TextDialogGptCompletion,
        prompt_settings=ASK_EVERYTHING_PROMPT,
        temperature=0.0,
    ),
]
