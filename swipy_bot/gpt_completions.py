# pylint: disable=too-many-instance-attributes,too-few-public-methods,too-many-arguments
import random
import traceback
from dataclasses import dataclass
from datetime import datetime

import openai
from asgiref.sync import sync_to_async

from swipy_app.models import GptCompletion, TelegramUpdate, Utterance, SwipyUser
from swipy_bot.swipy_config import MOCK_GPT, MAX_CONVERSATION_LENGTH


@dataclass(frozen=True)
class GptPromptSettings:
    prompt_name: str
    prompt_template: str
    append_bot_name_at_the_end: bool = True
    double_newline_between_utterances: bool = True


@dataclass(frozen=True)
class GptCompletionSettings:
    prompt_settings: GptPromptSettings
    engine: str = "text-davinci-003"
    max_tokens: int = 512  # OpenAI's default is 16
    temperature: float = 1.0  # Possible range - from 0.0 to 2.0
    top_p: float = 1.0  # Possible range - from 0.0 to 1.0
    frequency_penalty: float = 0.0  # Possible range - from -2.0 to 2.0
    presence_penalty: float = 0.0  # Possible range - from -2.0 to 2.0


class DialogGptCompletion:
    def __init__(
        self,
        settings: GptCompletionSettings,
        bot_name: str,
        swipy_user: SwipyUser,
    ):
        self.settings = settings
        self.bot_name = bot_name
        self.swipy_user = swipy_user

        self.user_first_name = self.swipy_user.first_name
        self.user_prefix = self.utterance_prefix(self.user_first_name)
        self.bot_prefix = self.utterance_prefix(self.bot_name)

        self.gpt_completion_in_db: GptCompletion | None = None
        # TODO oleksandr: there are times when you don't need this stop list, for ex. when you're summarizing
        self.stop_list = [
            # "\n",  # TODO oleksandr: enable this if it's the very first exchange ?
            self.user_prefix,
            self.bot_prefix,
        ]

        self.completion: str | None = None
        self.prompt: str | None = None

    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}:*"

    async def build_prompt(
        self,
        conversation_id: int,
        stop_before_utterance: Utterance | None = None,
    ) -> None:
        prompt_parts = []

        utterances = Utterance.objects.filter(conversation_id=conversation_id).order_by("-arrival_timestamp_ms")
        # TODO oleksandr: replace MAX_CONVERSATION_LENGTH with a more sophisticated logic
        if stop_before_utterance:
            # pretend that the last utterance was the one before the stop_before_utterance
            utterances = await sync_to_async(list)(utterances)
            for idx, utterance in enumerate(utterances):
                if utterance.id == stop_before_utterance.pk:
                    utterances = utterances[idx + 1 :]
                    break
            utterances = utterances[:MAX_CONVERSATION_LENGTH]
        else:
            # don't pretend, just take the last MAX_CONVERSATION_LENGTH utterances
            utterances = utterances[:MAX_CONVERSATION_LENGTH]
            utterances = await sync_to_async(list)(utterances)

        for utterance in reversed(utterances):
            if not utterance.is_bot and utterance.text == "/start":
                # don't include /start in the prompt
                continue

            if utterance.is_bot:
                utterance_prefix = self.bot_prefix
            else:
                utterance_prefix = self.user_prefix
            prompt_parts.append(f"{utterance_prefix} {utterance.text}")

        if self.settings.prompt_settings.append_bot_name_at_the_end:
            if stop_before_utterance and not stop_before_utterance.is_bot:
                # we are trying to mimic the user, not the bot
                prompt_parts.append(self.user_prefix)
            else:
                prompt_parts.append(self.bot_prefix)

        utterance_delimiter = "\n\n" if self.settings.prompt_settings.double_newline_between_utterances else "\n"
        dialog = utterance_delimiter.join(prompt_parts)
        self.prompt = self.settings.prompt_settings.prompt_template.format(
            DIALOG=dialog,
            USER=self.user_first_name,
            BOT=self.bot_name,
        )

    async def fulfil(
        self,
        conversation_id: int,
        tg_update_in_db: TelegramUpdate | None = None,
        stop_before_utterance: Utterance | None = None,
    ) -> None:
        await self.build_prompt(
            conversation_id=conversation_id,
            stop_before_utterance=stop_before_utterance,
        )

        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        request_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        self.gpt_completion_in_db = await GptCompletion.objects.acreate(
            request_timestamp_ms=request_timestamp_ms,
            triggering_update=tg_update_in_db,
            swipy_user_id=self.swipy_user.pk,
            prompt=self.prompt,
            prompt_name=self.settings.prompt_settings.prompt_name,
            engine=self.settings.engine,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            top_p=self.settings.top_p,
            frequency_penalty=self.settings.frequency_penalty,
            presence_penalty=self.settings.presence_penalty,
        )

        try:
            if MOCK_GPT:
                # await asyncio.sleep(1)
                self.completion = f"\n\nHERE GOES GPT RESPONSE (IT'S A MOCK!) {random.randint(0, 10000)}"
            else:
                gpt_response = await openai.Completion.acreate(
                    # TODO oleksandr: submit user id from Telegram (or from your database) too
                    prompt=self.gpt_completion_in_db.prompt,
                    stop=self.stop_list,
                    engine=self.gpt_completion_in_db.engine,
                    max_tokens=self.gpt_completion_in_db.max_tokens,
                    temperature=self.gpt_completion_in_db.temperature,
                    top_p=self.gpt_completion_in_db.top_p,
                    frequency_penalty=self.gpt_completion_in_db.frequency_penalty,
                    presence_penalty=self.gpt_completion_in_db.presence_penalty,
                )
                self.completion = gpt_response.choices[0].text
                assert (
                    len(gpt_response.choices) == 1
                ), f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
        except Exception:
            # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
            arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
            self.gpt_completion_in_db.arrival_timestamp_ms = arrival_timestamp_ms
            self.gpt_completion_in_db.completion = f"===== ERROR =====\n\n{traceback.format_exc()}"
            await sync_to_async(self.gpt_completion_in_db.save)(update_fields=["arrival_timestamp_ms", "completion"])
            raise

        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
        self.gpt_completion_in_db.arrival_timestamp_ms = arrival_timestamp_ms
        self.gpt_completion_in_db.completion = self.completion
        await sync_to_async(self.gpt_completion_in_db.save)(update_fields=["arrival_timestamp_ms", "completion"])


class DialogGptCompletionFactory:  # TODO oleksandr: extend from GptCompletionSettings (a frozen dataclass)
    def __init__(
        self,
        settings: GptCompletionSettings,
        bot_name: str,
    ):
        self.settings = settings
        self.bot_name = bot_name

    def new_completion(self, swipy_user: SwipyUser) -> DialogGptCompletion:
        gpt_completion = DialogGptCompletion(
            settings=self.settings,
            bot_name=self.bot_name,
            swipy_user=swipy_user,
        )
        return gpt_completion
