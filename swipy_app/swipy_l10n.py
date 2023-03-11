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
    BTN_LANGUAGE: str = "Language / Мова 🌐"
    BTN_MAIN_MENU: str = "Main menu 🏠"
    BTN_EXPAND_ON_THIS: str = "Expand on this 📚"
    BTN_THANKS: str = "Thanks 🌟"
    BTN_NOT_HELPFUL: str = "Not helpful 💔"
    BTN_PROCEED_WITH_SUBJECT: str = "Let's proceed with this subject 📚"

    MSG_START_TEMPLATE: str = "Hi {USER}! My name is {BOT}🤖\n\nHow can I help you? 😊"
    MSG_MAIN_MENU: str = "Sure, what would you like?"

    MSG_CHOOSE_LANGUAGE: str = "Choose your language / Оберіть мову 🌐"
    BTN_ENGLISH: str = "English 🇬🇧"
    BTN_UKRAINIAN: str = "Українська 🇺🇦"


LANGUAGES = {
    "en": SwipyL10n(),
    "uk": SwipyL10n(
        MAX_CONVERSATION_LENGTH=10,
        BTN_I_JUST_WANT_TO_CHAT="Хочу просто поговорити 😊",
        BTN_SMTH_IS_BOTHERING_ME="Мене щось турбує 😔",
        BTN_HELP_ME_FIGHT_PROCRAST="Допоможи з прокрастинацією ✅",
        BTN_SOMETHING_ELSE="Щось інше 🤔",
        BTN_MAIN_MENU="Головне меню 🏠",
        BTN_EXPAND_ON_THIS="Детальніше 📚",
        BTN_THANKS="Дякую 🌟",
        BTN_NOT_HELPFUL="Не допомогло 💔",
        BTN_PROCEED_WITH_SUBJECT="Продовжуймо цю тему 📚",
        MSG_START_TEMPLATE="Привіт {USER}! Мене звати {BOT}🤖\n\nЯк я можу тобі допомогти? 😊",
        MSG_MAIN_MENU="Звичайно, що тебе цікавить?",
    ),
}
DEFAULT_LANG = LANGUAGES["en"]
