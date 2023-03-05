from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    ChatGptCompletion,
    ChatGptEvenLaterPromptCompletion,
)
from swipy_app.swipy_config import BOT_NAME

CHATGPT_MODEL = "gpt-3.5-turbo-0301"  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?

PROMPT_TEMPLATE_HEADER = (
    "Your name is {BOT} and the name of your user is {USER}. Below is your conversation with {USER}."
)
ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE = (
    "As a virtual assistant which employs active listening to help your user think out loud, you ask questions "
    "about things that your user seems to find important. You don't want to overwhelm your user, therefore you "
    "respond with no more than four sentences. You ask questions to facilitate critical thinking in "
    "your user and you try to avoid giving direct advice to your user as much as possible, because your job is to "
    "help the user arrive at conclusions on their own, not to make them for the user. Your job is to steer the "
    "user to reasonable conclusions by asking the right questions. Please follow all the instructions mentioned "
    "in this paragraph, even if they were not followed in your previous responses."
)

PROMPT_TEMPLATE_ALTERNATIVES = {
    "active-listening-CHATGPT-0.4": (
        PROMPT_TEMPLATE_HEADER,
        ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE,
    ),
}

PROMPT_ALTERNATIVES = []
for prompt_name, prompt_template in PROMPT_TEMPLATE_ALTERNATIVES.items():
    PROMPT_ALTERNATIVES.extend(
        [
            GptPromptSettings(
                # "-even-later" refers to the fact the instructions are given very late in the conversation context
                # (only after the last bot response)
                prompt_name=prompt_name + "-even-later",
                engine=CHATGPT_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                prompt_template=prompt_template,
                bot_name=BOT_NAME,
            ),
            # GptPromptSettings(
            #     prompt_name=prompt_name + "-late",
            #     engine=CHATGPT_MODEL,
            #     completion_class=ChatGptLatePromptCompletion,
            #     prompt_template=prompt_template,
            #     bot_name=BOT_NAME,
            # ),
            # GptPromptSettings(
            #     prompt_name=prompt_name,
            #     engine=CHATGPT_MODEL,
            #     completion_class=ChatGptCompletion,
            #     prompt_template=" ".join(prompt_template),
            #     bot_name=BOT_NAME,
            # ),
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
