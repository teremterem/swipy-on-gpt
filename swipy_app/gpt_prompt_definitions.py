from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    ChatGptEvenLaterPromptCompletion,
    ChatGptCompletion,
)
from swipy_app.swipy_config import BOT_NAME

CHATGPT_MODEL = "gpt-3.5-turbo-0301"  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?

PROMPT_TEMPLATE_HEADER = (
    "Your name is {BOT} and the name of your user is {USER}. Below is your conversation with {USER}."
)
ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE = (
    "As a virtual assistant, your role is to employ active listening to encourage users to think out loud. "
    "Your message should be no more than three sentences long and should ask open-ended questions about "
    "topics that seem important to the user. The purpose of these questions is to facilitate critical "
    "thinking in the user and guide them towards considering different perspectives and options. Avoid "
    "giving direct advice, as your job is to help the user arrive at conclusions on their own. Ensure "
    "that your next message follows these instructions, even if previous messages did not."
)
PROMPT_TEMPLATE_ALTERNATIVES = {
    "active-listening-CHATGPT-0.7": (
        PROMPT_TEMPLATE_HEADER,
        ACTIVE_LISTENING_MANUAL_PROMPT_TEMPLATE,
    ),
}

PROMPT_ALTERNATIVES = []
for prompt_name, prompt_template in PROMPT_TEMPLATE_ALTERNATIVES.items():
    PROMPT_ALTERNATIVES.extend(
        [
            GptPromptSettings(
                prompt_name=prompt_name,
                engine=CHATGPT_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                prompt_template=prompt_template,
                bot_name=BOT_NAME,
            ),
            # GptPromptSettings(
            #     prompt_name=prompt_name + "-prompt-before-bot",
            #     engine=CHATGPT_MODEL,
            #     completion_class=ChatGptLatePromptCompletion,
            #     prompt_template=prompt_template,
            #     bot_name=BOT_NAME,
            # ),
            # GptPromptSettings(
            #     prompt_name=prompt_name + "-prompt-before-chat",
            #     engine=CHATGPT_MODEL,
            #     completion_class=ChatGptCompletion,
            #     prompt_template=" ".join(prompt_template),
            #     bot_name=BOT_NAME,
            # ),
        ],
    )
PROMPT_ALTERNATIVES.append(
    GptPromptSettings(
        prompt_name="CHATGPT-NO-PROMPT",
        engine=CHATGPT_MODEL,
        completion_class=ChatGptCompletion,
        prompt_template=None,
        bot_name=BOT_NAME,
    ),
)

COMPLETION_CONFIG_ALTERNATIVES = []
for prompt_config in PROMPT_ALTERNATIVES:
    COMPLETION_CONFIG_ALTERNATIVES.extend(
        [
            GptCompletionSettings(
                prompt_settings=prompt_config,
                temperature=1.0,
                top_p=1.0,
            ),
            GptCompletionSettings(
                prompt_settings=prompt_config,
                temperature=0.0,
                top_p=1.0,
            ),
            # GptCompletionSettings(
            #     prompt_settings=prompt_config,
            #     temperature=1.0,
            #     top_p=0.0,  # produces exactly the same text as top_p=1.0 and temperature=0.0
            # ),
        ],
    )

MAIN_COMPLETION_CONFIG = COMPLETION_CONFIG_ALTERNATIVES[0]
