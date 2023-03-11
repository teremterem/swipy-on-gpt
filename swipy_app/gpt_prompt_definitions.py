from typing import Iterable

from swipy_app.gpt_completions import (
    GptPromptSettings,
    GptCompletionSettings,
    ChatGptEvenLaterPromptCompletion,
    ChatGptCompletion,
    TextDialogGptCompletion,
)
from swipy_app.swipy_config import BOT_NAME


def _generate_completion_config_alternatives(
    prompt_configs: Iterable[GptPromptSettings],
) -> tuple[GptCompletionSettings, ...]:
    alternatives = []
    for prompt_config in prompt_configs:
        alternatives.extend(
            [
                GptCompletionSettings(
                    prompt_settings=prompt_config,
                    temperature=0.0,
                    top_p=1.0,
                ),
                GptCompletionSettings(
                    prompt_settings=prompt_config,
                    temperature=1.0,
                    top_p=1.0,
                ),
                # GptCompletionSettings(
                #     prompt_settings=prompt_config,
                #     temperature=1.0,
                #     top_p=0.0,  # produces exactly the same text as top_p=1.0 and temperature=0.0
                # ),
            ]
        )
    return tuple(alternatives)


CHATGPT_U_MODEL = "gpt-3.5-turbo"  # TODO oleksandr: compare with "gpt-3.5-turbo-0301" ?
# CHATGPT_MODEL = "gpt-3.5-turbo-0301"
DAVINCI_MODEL = "text-davinci-003"

PROMPT_HEADER_TEMPLATE: str = (
    "Your name is {BOT} and the name of your user is {USER}. Below is your conversation with {USER}."
)
ACTIVE_LISTENING_PROMPT_TEMPLATE: str = (
    "As a virtual assistant, your role is to employ active listening to encourage users to think out loud. "
    "Your message should be no more than three sentences long and should ask open-ended questions about "
    "topics that seem important to the user. The purpose of these questions is to facilitate critical "
    "thinking in the user. Avoid giving direct advice, as your job is to help the user arrive at "
    "conclusions on their own."
)
ENSURE_INSTRUCTIONS_FOLLOWED: str = (
    " Ensure that your next message follows these instructions, even if previous messages did not."
)

ACTIVE_LISTENING_CHATGPT_PROMPT_TEMPLATE = ACTIVE_LISTENING_PROMPT_TEMPLATE + ENSURE_INSTRUCTIONS_FOLLOWED

ASK_EVERYTHING_0_1_PROMPT_HEADER_TEMPLATE = (
    "Your name is {BOT} and the user's name is {USER}. Here is your dialog with {USER}."
)
ASK_EVERYTHING_0_1_PROMPT_TEMPLATE = (
    "If {USER} mentions any people, things, places, events etc. you don't know about (or if you don't "
    "know any details about mentioned people, things, places, events etc. in relation to {USER} "
    "specifically) then follow up with corresponding clarifying questions to {USER}."
)

GEN_ALT_BUTTONS = {
    ("chatgpt_alts", "ChatGPT alternatives"): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                # _U - receives updates
                prompt_name="active-listening-CHATGPT_U-0.8",
                prompt_template=(
                    PROMPT_HEADER_TEMPLATE,
                    ACTIVE_LISTENING_CHATGPT_PROMPT_TEMPLATE,
                ),
                engine=CHATGPT_U_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                bot_name=BOT_NAME,
            ),
            GptPromptSettings(
                # _U - receives updates
                prompt_name="active-listening-CHATGPT_U-0.8-early-prompt",
                prompt_template=" ".join(
                    [
                        PROMPT_HEADER_TEMPLATE,
                        ACTIVE_LISTENING_CHATGPT_PROMPT_TEMPLATE,
                    ]
                ),
                engine=CHATGPT_U_MODEL,
                completion_class=ChatGptCompletion,
                bot_name=BOT_NAME,
            ),
        ]
    ),
    ("chatgpt_no_prompt_alts", 'ChatGPT "no prompt"'): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                # _U - receives updates
                prompt_name="CHATGPT_U-NO-PROMPT",
                engine=CHATGPT_U_MODEL,
                completion_class=ChatGptCompletion,
                prompt_template=None,
                bot_name=BOT_NAME,
            ),
        ]
    ),
    ("davinci_alts", "Davinci alternatives"): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                prompt_name="active-listening-DAVINCI-0.8",
                prompt_template=" ".join(
                    [
                        PROMPT_HEADER_TEMPLATE,
                        ACTIVE_LISTENING_PROMPT_TEMPLATE,
                    ]
                )
                + "\n\n---\n\n{DIALOG}",
                engine=DAVINCI_MODEL,
                completion_class=TextDialogGptCompletion,
                bot_name=BOT_NAME,
            ),
        ]
    ),
    ("oldest_prompt_alts", "Oldest prompt"): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                prompt_name="ask-everything-0.1",
                prompt_template=" ".join(
                    [
                        ASK_EVERYTHING_0_1_PROMPT_HEADER_TEMPLATE,
                        ASK_EVERYTHING_0_1_PROMPT_TEMPLATE,
                    ]
                )
                + "\n\n{DIALOG}",
                double_newline_between_utterances=False,
                engine=DAVINCI_MODEL,
                completion_class=TextDialogGptCompletion,
                bot_name=BOT_NAME,
            ),
            GptPromptSettings(
                # _U - receives updates
                prompt_name="ask-everything-CHATGPT_U-0.1",
                prompt_template=(
                    ASK_EVERYTHING_0_1_PROMPT_HEADER_TEMPLATE,
                    ASK_EVERYTHING_0_1_PROMPT_TEMPLATE,
                ),
                engine=CHATGPT_U_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                bot_name=BOT_NAME,
            ),
            GptPromptSettings(
                # _U - receives updates
                prompt_name="ask-everything-CHATGPT-0.1_U-early-prompt",
                prompt_template=" ".join(
                    [
                        ASK_EVERYTHING_0_1_PROMPT_HEADER_TEMPLATE,
                        ASK_EVERYTHING_0_1_PROMPT_TEMPLATE,
                    ]
                ),
                engine=CHATGPT_U_MODEL,
                completion_class=ChatGptCompletion,
                bot_name=BOT_NAME,
            ),
        ]
    ),
}

MAIN_COMPLETION_CONFIG = GEN_ALT_BUTTONS[("chatgpt_alts", "ChatGPT alternatives")][0]
assert MAIN_COMPLETION_CONFIG.prompt_settings.prompt_name == "active-listening-CHATGPT_U-0.8"
assert MAIN_COMPLETION_CONFIG.temperature == 0.0

NO_PROMPT_COMPLETION_CONFIG = GEN_ALT_BUTTONS[("chatgpt_no_prompt_alts", 'ChatGPT "no prompt"')][0]
assert NO_PROMPT_COMPLETION_CONFIG.prompt_settings.prompt_name == "CHATGPT_U-NO-PROMPT"
assert NO_PROMPT_COMPLETION_CONFIG.temperature == 0.0
