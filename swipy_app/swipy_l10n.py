# pylint: disable=invalid-name,too-many-instance-attributes
from dataclasses import dataclass


# TODO oleksandr: replace with Django l10n ?
@dataclass(frozen=True)
class SwipyL10n:
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
