from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    ChatGptCompletion,
    ChatGptLatePromptCompletion,
    ChatGptEvenLaterPromptCompletion,
)
from swipy_app.swipy_config import BOT_NAME

CHATGPT_MODEL = "gpt-3.5-turbo-0301"  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?

PROMPT_TEMPLATE_HEADER = (
    "Your name is {BOT} and the name of your user is {USER}. Below is your conversation with {USER}."
)
ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE = (
    "As an assistant that employs active listening to help your user think out loud, you ask questions about things "
    "that your user seems to find important. You don't want to overwhelm your user, hence your responses are short. "
    "You ask questions to facilitate critical thinking in your user. You want your user to arrive at their own "
    "conclusions, hence you try to avoid giving direct advice as much as possible."
)

PROMPT_TEMPLATE_ALTERNATIVES = {
    "listening-CHATGPT-MANUAL-0.2": (
        PROMPT_TEMPLATE_HEADER,
        ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE,
    ),
    "listening-CHATGPT-MANUAL-0.2-QUE-EXC": (
        PROMPT_TEMPLATE_HEADER,
        f"{ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE} The only exception to the rule of not giving direct advice is "
        f"when there are no more good questions to ask.",
    ),
    "listening-CHATGPT-AUTO-0.2": (
        PROMPT_TEMPLATE_HEADER,
        "As an assistant that employs active listening to help your user think out loud, you identify what is the most "
        "important information your user is conveying and respond accordingly.",
    ),
}

PROMPT_ALTERNATIVES = []
for prompt_name, prompt_template in PROMPT_TEMPLATE_ALTERNATIVES.items():
    PROMPT_ALTERNATIVES.extend(
        [
            GptPromptSettings(
                prompt_name=prompt_name + "-late",
                engine=CHATGPT_MODEL,
                completion_class=ChatGptLatePromptCompletion,
                prompt_template=prompt_template,
                bot_name=BOT_NAME,
            ),
            GptPromptSettings(
                prompt_name=prompt_name + "-even-later",
                engine=CHATGPT_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                prompt_template=prompt_template,
                bot_name=BOT_NAME,
            ),
            GptPromptSettings(
                prompt_name=prompt_name,
                engine=CHATGPT_MODEL,
                completion_class=ChatGptCompletion,
                prompt_template=" ".join(prompt_template),
                bot_name=BOT_NAME,
            ),
        ]
    )
PROMPT_ALTERNATIVES.append(
    GptPromptSettings(
        prompt_name="CHATGPT-NO-PROMPT",
        engine=CHATGPT_MODEL,
        completion_class=ChatGptCompletion,
        prompt_template=None,
        bot_name=BOT_NAME,
    )
)

COMPLETION_CONFIG_ALTERNATIVES = []
for prompt_config in PROMPT_ALTERNATIVES:
    COMPLETION_CONFIG_ALTERNATIVES.append(
        GptCompletionSettings(
            prompt_settings=prompt_config,
            temperature=1.0,
        )
    )

MAIN_COMPLETION_CONFIG = COMPLETION_CONFIG_ALTERNATIVES[0]
