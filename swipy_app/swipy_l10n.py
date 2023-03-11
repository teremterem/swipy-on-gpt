# pylint: disable=invalid-name,too-many-instance-attributes
from dataclasses import dataclass


# TODO oleksandr: replace with Django l10n
@dataclass(frozen=True)
class SwipyL10n:
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
    PROMPT_CONFIG_NAME_SUFFIX: str = ""

    MAX_CONVERSATION_LENGTH: int = 40

    BTN_I_JUST_WANT_TO_CHAT: str = "I just wanna chat 😊"
    BTN_SMTH_IS_BOTHERING_ME: str = "Something’s bothering me 😔"
    BTN_HELP_ME_FIGHT_PROCRAST: str = "Help me fight procrastination ✅"
    BTN_SOMETHING_ELSE: str = "Something else 🤔"
    BTN_MAIN_MENU: str = "Main menu 🏠"
    BTN_EXPAND_ON_THIS: str = "Expand on this 📚"
    BTN_THANKS: str = "Thanks 🌟"
    BTN_NOT_HELPFUL: str = "Not helpful 💔"
    BTN_PROCEED_WITH_SUBJECT: str = "Let's proceed with this subject 📚"


DefaultLang = SwipyL10n()
