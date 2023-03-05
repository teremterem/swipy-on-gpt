from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    TextDialogGptCompletion,
    ChatGptCompletion,
)
from swipy_app.swipy_config import BOT_NAME

ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE = (
    "Your name is {BOT} and your user's name is {USER}. Below is your conversation with {USER}. As an assistant "
    "that employs active listening to help your user think out loud, you listen to {USER} carefully, identify "
    "things that are of most importance to {USER} and ask questions on those things to facilitate critical "
    "thinking in {USER}. You don't want to overwhelm your user, hence your responses are short and concise. "
    "You want your user to arrive at their own conclusions, hence you try to avoid giving direct advice as much as "
    "possible and ask questions instead (the only exception to this is when there are no more good questions to ask)."
)
ACTIVE_LISTENING_AUTO_PROMPT_TEMPLATE = (
    "Your name is {BOT} and the user's name is {USER}. Below is your conversation with {USER}. As a assistant "
    "that employs active listening to help your user think out loud, you identify what is the most important "
    "information {USER} is conveying and respond accordingly."
)
ASK_EVERYTHING_PROMPT_TEMPLATE = (
    "Your name is {BOT} and the user's name is {USER}. Below is your conversation with {USER}. If {USER} "
    "mentions any people, things, places, events etc. you don't know about (or if you don't know details about "
    "mentioned people, things, places, events etc. in relation to {USER} specifically) then follow up with "
    "corresponding clarifying questions to {USER}."
)

PROMPT_ALTERNATIVES = [
    GptPromptSettings(
        prompt_name="active-listening-CHATGPT-MANUAL-0.1",
        engine="gpt-3.5-turbo-0301",  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?
        completion_class=ChatGptCompletion,
        prompt_template=ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE,
        bot_name=BOT_NAME,
    ),
    GptPromptSettings(
        prompt_name="active-listening-DAVINCI-MANUAL-0.1",
        engine="text-davinci-003",
        completion_class=TextDialogGptCompletion,
        prompt_template=ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE + "\n\n---\n\n{DIALOG}",
        bot_name=BOT_NAME,
    ),
    GptPromptSettings(
        prompt_name="active-listening-CHATGPT-AUTO-0.1",
        engine="gpt-3.5-turbo-0301",  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?
        completion_class=ChatGptCompletion,
        prompt_template=ACTIVE_LISTENING_AUTO_PROMPT_TEMPLATE,
        bot_name=BOT_NAME,
    ),
    GptPromptSettings(
        prompt_name="active-listening-DAVINCI-AUTO-0.1",
        engine="text-davinci-003",
        completion_class=TextDialogGptCompletion,
        prompt_template=ACTIVE_LISTENING_AUTO_PROMPT_TEMPLATE + "\n\n---\n\n{DIALOG}",
        bot_name=BOT_NAME,
    ),
    GptPromptSettings(
        prompt_name="chatgpt-ask-everything-0.1",
        engine="gpt-3.5-turbo-0301",  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?
        completion_class=ChatGptCompletion,
        prompt_template=ASK_EVERYTHING_PROMPT_TEMPLATE,
        bot_name=BOT_NAME,
    ),
    GptPromptSettings(
        prompt_name="ask-everything-0.3",
        engine="text-davinci-003",
        completion_class=TextDialogGptCompletion,
        prompt_template=ASK_EVERYTHING_PROMPT_TEMPLATE + "\n\n---\n\n{DIALOG}",
        bot_name=BOT_NAME,
    ),
]

COMPLETION_CONFIG_ALTERNATIVES = []
for prompt_config in PROMPT_ALTERNATIVES:
    COMPLETION_CONFIG_ALTERNATIVES.append(
        GptCompletionSettings(
            prompt_settings=prompt_config,
            temperature=1.0,
        )
    )
    COMPLETION_CONFIG_ALTERNATIVES.append(
        GptCompletionSettings(
            prompt_settings=prompt_config,
            temperature=0.0,
        )
    )

MAIN_COMPLETION_CONFIG = COMPLETION_CONFIG_ALTERNATIVES[0]
