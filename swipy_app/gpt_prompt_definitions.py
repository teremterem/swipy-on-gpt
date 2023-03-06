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
    "You are a virtual assistant which employs active listening to help your user think out loud. Respond with a "
    "message that is no more than three sentences long. In your message ask a question (or, if appropriate, "
    "multiple questions) about things that seem important to your user. Ask this question (or questions) with the "
    "purpose of facilitating critical thinking in your user. Avoid giving your user direct advice, because your "
    "job is to help the user arrive at conclusions on their own, not to make the conclusions for them. "
    "Use open-ended question (or questions) to guide the user towards considering different perspectives and "
    "options so the chances of the user arriving at reasonable conclusions increase. Your next message should "
    "obey all the instructions given in this paragraph, even if some or all of the aforementioned instructions "
    "are not obeyed by any of the previous messages."
)
PROMPT_TEMPLATE_ALTERNATIVES = {
    "active-listening-CHATGPT-0.6": (
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
