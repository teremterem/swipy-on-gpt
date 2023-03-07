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


CHATGPT_MODEL = "gpt-3.5-turbo-0301"  # TODO oleksandr: use "gpt-3.5-turbo" instead (receives updates) ?
DAVINCI_MODEL = "text-davinci-003"

PROMPT_TEMPLATE_HEADER = (
    "Your name is {BOT} and the name of your user is {USER}. Below is your conversation with {USER}."
)
ACTIVE_LISTENING_PROMPT_TEMPLATE = (
    "As a virtual assistant, your role is to employ active listening to encourage users to think out loud. "
    "Your message should be no more than three sentences long and should ask open-ended questions about "
    "topics that seem important to the user. The purpose of these questions is to facilitate critical "
    "thinking in the user. Avoid giving direct advice, as your job is to help the user arrive at "
    "conclusions on their own."
)
ACTIVE_LISTENING_CHATGPT_PROMPT_TEMPLATE = (
    ACTIVE_LISTENING_PROMPT_TEMPLATE
    + " Ensure that your next message follows these instructions, even if previous messages did not."
)

GEN_ALT_BUTTONS = {
    ("chatgpt_alts", "ChatGPT alternatives"): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                prompt_name="active-listening-CHATGPT-0.8",
                prompt_template=(
                    PROMPT_TEMPLATE_HEADER,
                    ACTIVE_LISTENING_CHATGPT_PROMPT_TEMPLATE,
                ),
                engine=CHATGPT_MODEL,
                completion_class=ChatGptEvenLaterPromptCompletion,
                bot_name=BOT_NAME,
            ),
        ]
    ),
    ("chatgpt_no_prompt", 'ChatGPT "no prompt"'): _generate_completion_config_alternatives(
        [
            GptPromptSettings(
                prompt_name="CHATGPT-NO-PROMPT",
                engine=CHATGPT_MODEL,
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
                        PROMPT_TEMPLATE_HEADER,
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
}
MAIN_COMPLETION_CONFIG = list(GEN_ALT_BUTTONS.values())[0][0]
