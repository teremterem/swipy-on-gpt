from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    TextDialogGptCompletion,
    ChatGptCompletion,
)
from swipy_app.swipy_config import BOT_NAME

ASK_EVERYTHING_PROMPT_TEMPLATE = (
    "Your name is {BOT} and the user's name is {USER}. Below is your conversation with {USER}. If {USER} "
    "mentions any people, things, places, events etc. you don't know about (or if you don't know details about "
    "mentioned people, things, places, events etc. in relation to {USER} specifically) then follow up with "
    "corresponding clarifying questions to {USER}."
)

ASK_EVERYTHING_CHATGPT_PROMPT = GptPromptSettings(
    prompt_name="chatgpt-ask-everything-0.1",
    engine="gpt-3.5-turbo-0301",  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?
    completion_class=ChatGptCompletion,
    prompt_template=ASK_EVERYTHING_PROMPT_TEMPLATE,
    bot_name=BOT_NAME,
)
ASK_EVERYTHING_DAVINCI_PROMPT = GptPromptSettings(
    prompt_name="ask-everything-0.3",
    engine="text-davinci-003",
    completion_class=TextDialogGptCompletion,
    prompt_template=ASK_EVERYTHING_PROMPT_TEMPLATE + "\n\n---\n\n{DIALOG}",
    bot_name=BOT_NAME,
)

MAIN_COMPLETION_CONFIG = GptCompletionSettings(
    prompt_settings=ASK_EVERYTHING_CHATGPT_PROMPT,
)  # temperature=1.0 (default)

CHATGPT_COMPLETION_CONFIG_ALTERNATIVES = [
    MAIN_COMPLETION_CONFIG,  # temperature=1.0 (default)
    GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_CHATGPT_PROMPT,
        temperature=0.5,
    ),
    GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_CHATGPT_PROMPT,
        temperature=0.0,
    ),
]
DAVINCI_COMPLETION_CONFIG_ALTERNATIVES = [
    GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_DAVINCI_PROMPT,
    ),  # temperature=1.0 (default)
    GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_DAVINCI_PROMPT,
        temperature=0.5,
    ),
    GptCompletionSettings(
        prompt_settings=ASK_EVERYTHING_DAVINCI_PROMPT,
        temperature=0.0,
    ),
]
