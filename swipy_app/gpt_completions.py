# pylint: disable=too-many-instance-attributes,too-few-public-methods
import random
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pprint import pformat
from typing import Any

import openai
from asgiref.sync import sync_to_async

from swipy_app.models import GptCompletion, TelegramUpdate, Utterance, SwipyUser
from swipy_app.swipy_config import MOCK_GPT, MAX_CONVERSATION_LENGTH
from swipy_app.swipy_utils import current_time_utc_ms


@dataclass(frozen=True)
class GptPromptSettings:
    prompt_name: str
    prompt_template: str | tuple[str, ...] | None
    completion_class: type["BaseDialogGptCompletion"]
    engine: str
    bot_name: str
    append_bot_name_at_the_end: bool = True  # TODO oleksandr: check if it is needed in case of ChatGptCompletion
    double_newline_between_utterances: bool = True  # TODO oleksandr: irrelevant in case of ChatGptCompletion


@dataclass(frozen=True)
class GptCompletionSettings:
    prompt_settings: GptPromptSettings
    max_tokens: int = 512  # OpenAI's default is 16
    temperature: float = 1.0  # Possible range - from 0.0 to 2.0
    top_p: float = 1.0  # Possible range - from 0.0 to 1.0
    frequency_penalty: float = 0.0  # Possible range - from -2.0 to 2.0
    presence_penalty: float = 0.0  # Possible range - from -2.0 to 2.0

    def new_completion(self, swipy_user: SwipyUser) -> "BaseDialogGptCompletion":
        return self.prompt_settings.completion_class(
            settings=self,
            swipy_user=swipy_user,
        )

    async def fulfil_completion(
        self,
        swipy_user: SwipyUser,
        conversation_id: int,
        tg_update_in_db: TelegramUpdate | None = None,
        stop_before_utterance: Utterance | None = None,
    ):
        completion = self.new_completion(swipy_user)
        await completion.fulfil(
            conversation_id=conversation_id,
            tg_update_in_db=tg_update_in_db,
            stop_before_utterance=stop_before_utterance,
        )
        return completion


class BaseDialogGptCompletion(ABC):
    def __init__(
        self,
        settings: GptCompletionSettings,
        swipy_user: SwipyUser,
    ):
        self.settings = settings
        self.swipy_user = swipy_user

        self.context_utterances: list[Utterance] | None = None
        self.gpt_completion_in_db: GptCompletion | None = None

        self.prompt_raw: Any | None = None
        self.prompt_str: str | None = None
        self.completion: str | None = None

    @abstractmethod
    async def _build_raw_prompt(self, stop_before_utterance: Utterance | None = None) -> Any:
        pass

    @abstractmethod
    async def _make_openai_call(self) -> str:
        pass

    def _convert_raw_prompt_to_str(self) -> str:
        return str(self.prompt_raw)

    # noinspection PyMethodMayBeStatic
    async def _prepare_context_utterances(
        self,
        conversation_id: int,
        stop_before_utterance: Utterance | None = None,
    ) -> list[Utterance]:
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

        utterances = [
            utterance
            for utterance in reversed(utterances)
            if utterance.is_bot or utterance.text != "/start"  # don't include /start (from user) in the prompt
        ]
        return utterances

    async def fulfil(
        self,
        conversation_id: int,
        tg_update_in_db: TelegramUpdate | None = None,
        stop_before_utterance: Utterance | None = None,
    ) -> None:
        self.context_utterances = await self._prepare_context_utterances(
            conversation_id=conversation_id,
            stop_before_utterance=stop_before_utterance,
        )
        self.prompt_raw = await self._build_raw_prompt(stop_before_utterance=stop_before_utterance)
        self.prompt_str = self._convert_raw_prompt_to_str()

        self.gpt_completion_in_db = await GptCompletion.objects.acreate(
            request_timestamp_ms=current_time_utc_ms(),
            triggering_update=tg_update_in_db,
            swipy_user_id=self.swipy_user.pk,
            prompt=self.prompt_str,
            prompt_name=self.settings.prompt_settings.prompt_name,
            engine=self.settings.prompt_settings.engine,
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
                self.completion = await self._make_openai_call()
        except Exception:
            self.gpt_completion_in_db.arrival_timestamp_ms = current_time_utc_ms()
            self.gpt_completion_in_db.completion = f"===== ERROR =====\n\n{traceback.format_exc()}"
            await sync_to_async(self.gpt_completion_in_db.save)()
            raise

        self.gpt_completion_in_db.arrival_timestamp_ms = current_time_utc_ms()
        self.gpt_completion_in_db.completion = self.completion
        await sync_to_async(self.gpt_completion_in_db.save)()


class TextDialogGptCompletion(BaseDialogGptCompletion):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_prefix = self.utterance_prefix(self.swipy_user.first_name)
        self.bot_prefix = self.utterance_prefix(self.settings.prompt_settings.bot_name)
        self.stop_list = [
            # "\n",  # TODO oleksandr: enable this if it's the very first exchange ?
            self.user_prefix,
            self.bot_prefix,
        ]

    # noinspection PyMethodMayBeStatic
    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}:*"

    async def _build_raw_prompt(self, stop_before_utterance: Utterance | None = None) -> Any:
        prompt_parts = []

        for utterance in self.context_utterances:
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
        if self.settings.prompt_settings.prompt_template:
            prompt = self.settings.prompt_settings.prompt_template.format(
                DIALOG=dialog,
                USER=self.swipy_user.first_name,
                BOT=self.settings.prompt_settings.bot_name,
            )
        else:
            prompt = dialog
        return prompt

    async def _make_openai_call(self) -> str:
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
        self.gpt_completion_in_db.full_api_response = gpt_response
        # TODO oleksandr: are you sure the following assertion in necessary at all?
        assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
        return gpt_response.choices[0].text


class ChatGptCompletion(BaseDialogGptCompletion):
    def _build_system_message(self, prompt_template: str) -> dict[str, str]:
        sys_message = {
            "content": prompt_template.format(
                USER=self.swipy_user.first_name,
                BOT=self.settings.prompt_settings.bot_name,
            ),
            "role": "system",
        }
        return sys_message

    # noinspection PyMethodMayBeStatic
    def _append_messages(self, messages: list[dict[str, str]], utterances_to_append: list[Utterance]) -> None:
        for utterance in utterances_to_append:
            messages.append(
                {
                    "content": utterance.text,
                    "role": "assistant" if utterance.is_bot else "user",
                }
            )

    async def _build_raw_prompt(self, stop_before_utterance: Utterance | None = None) -> Any:
        messages = []
        if self.settings.prompt_settings.prompt_template:
            messages = [self._build_system_message(self.settings.prompt_settings.prompt_template)]

        self._append_messages(messages, self.context_utterances)
        return messages

    def _convert_raw_prompt_to_str(self) -> str:
        return pformat(self.prompt_raw, sort_dicts=False)

    async def _make_openai_call(self) -> str:
        assert self.context_utterances, "Expected at least one utterance in the context, cannot call GPT without it"

        gpt_response = await openai.ChatCompletion.acreate(
            # TODO oleksandr: submit user id from Telegram (or from your database) too
            messages=self.prompt_raw,  # this time it's a list of dicts
            model=self.gpt_completion_in_db.engine,
            max_tokens=self.gpt_completion_in_db.max_tokens,
            temperature=self.gpt_completion_in_db.temperature,
            top_p=self.gpt_completion_in_db.top_p,
            frequency_penalty=self.gpt_completion_in_db.frequency_penalty,
            presence_penalty=self.gpt_completion_in_db.presence_penalty,
        )
        self.gpt_completion_in_db.full_api_response = gpt_response
        # TODO oleksandr: are you sure the following assertion in necessary at all?
        assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
        assert (
            gpt_response.choices[0].message.role == "assistant"
        ), f"Expected assistant's response, but got {gpt_response.choices[0].message.role}"
        return gpt_response.choices[0].message.content


class ChatGptLatePromptCompletion(ChatGptCompletion):
    def _idx_to_split_context_by(self) -> int:
        last_bot_utterance_index = None
        for idx, utterance in reversed(list(enumerate(self.context_utterances))):
            if utterance.is_bot:
                last_bot_utterance_index = idx
                break
        return last_bot_utterance_index

    async def _build_raw_prompt(self, stop_before_utterance: Utterance | None = None) -> Any:
        idx_to_split_context_by = self._idx_to_split_context_by()
        if idx_to_split_context_by is None:
            idx_to_split_context_by = 0

        messages = [self._build_system_message(self.settings.prompt_settings.prompt_template[0])]
        self._append_messages(messages, self.context_utterances[:idx_to_split_context_by])
        messages.append(self._build_system_message(self.settings.prompt_settings.prompt_template[1]))
        self._append_messages(messages, self.context_utterances[idx_to_split_context_by:])
        return messages


class ChatGptEvenLaterPromptCompletion(ChatGptLatePromptCompletion):
    def _idx_to_split_context_by(self) -> int:
        last_user_utterance_index = super()._idx_to_split_context_by()
        if last_user_utterance_index is not None:
            last_user_utterance_index += 1
        return last_user_utterance_index
