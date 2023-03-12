# pylint: disable=too-many-instance-attributes,too-few-public-methods
import random
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import openai
import tiktoken
from asgiref.sync import sync_to_async

from swipy_app.models import GptCompletion, TelegramUpdate, Utterance, SwipyUser, UtteranceConversation
from swipy_app.swipy_config import MOCK_GPT
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
    max_tokens: int = 1024  # OpenAI's default is 16
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
        stop_before_utt_conv: UtteranceConversation | None = None,
    ):
        completion = self.new_completion(swipy_user)
        await completion.fulfil(
            conversation_id=conversation_id,
            tg_update_in_db=tg_update_in_db,
            stop_before_utt_conv=stop_before_utt_conv,
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
        self.lang = swipy_user.get_lang()

        self.context_utterances: list[Utterance] | None = None
        self.gpt_completion_in_db: GptCompletion | None = None

        self.prompt_raw: Any | None = None
        self.prompt_str: str | None = None
        self.completion: str | None = None
        self.estimated_prompt_token_number: int | None = None

    @abstractmethod
    async def _build_raw_prompt(self, stop_before_utt_conv: UtteranceConversation | None = None) -> Any:
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
        stop_before_utt_conv: Utterance | None = None,
    ) -> list[Utterance]:
        # TODO oleksandr: there is no point in descending order and eventual reversal of the list (get rid of both)
        utt_conv_objects = (
            UtteranceConversation.objects.filter(conversation_id=conversation_id)
            .select_related("utterance")
            .order_by("-utterance__arrival_timestamp_ms")
        )

        # TODO oleksandr: replace self.lang.MAX_CONVERSATION_LENGTH with a more sophisticated logic
        if stop_before_utt_conv:
            # pretend that the last utterance was the one before the stop_before_utterance
            utt_conv_objects = await sync_to_async(list)(utt_conv_objects)
            for idx, utt_conv_object in enumerate(utt_conv_objects):
                if utt_conv_object.id == stop_before_utt_conv.pk:
                    utt_conv_objects = utt_conv_objects[idx + 1 :]
                    break
            utt_conv_objects = utt_conv_objects[: self.lang.MAX_CONVERSATION_LENGTH]
        else:
            # don't pretend, just take the last self.lang.MAX_CONVERSATION_LENGTH utterances
            utt_conv_objects = utt_conv_objects[: self.lang.MAX_CONVERSATION_LENGTH]
            utt_conv_objects = await sync_to_async(list)(utt_conv_objects)

        utterances = [utt_conv_object.utterance for utt_conv_object in reversed(utt_conv_objects)]
        return utterances

    async def fulfil(
        self,
        conversation_id: int,
        tg_update_in_db: TelegramUpdate | None = None,
        stop_before_utt_conv: UtteranceConversation | None = None,
    ) -> None:
        self.context_utterances = await self._prepare_context_utterances(
            conversation_id=conversation_id,
            stop_before_utt_conv=stop_before_utt_conv,
        )
        self.prompt_raw = await self._build_raw_prompt(stop_before_utt_conv=stop_before_utt_conv)
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
            estimated_prompt_token_number=self.estimated_prompt_token_number,
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

    async def _build_raw_prompt(self, stop_before_utt_conv: UtteranceConversation | None = None) -> Any:
        prompt_parts = []

        for utterance in self.context_utterances:
            if utterance.is_bot:
                utterance_prefix = self.bot_prefix
            else:
                utterance_prefix = self.user_prefix
            prompt_parts.append(f"{utterance_prefix} {utterance.text}")

        if self.settings.prompt_settings.append_bot_name_at_the_end:
            if stop_before_utt_conv and not stop_before_utt_conv.utterance.is_bot:
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

    async def _build_raw_prompt(self, stop_before_utt_conv: UtteranceConversation | None = None) -> Any:
        messages = []
        if self.settings.prompt_settings.prompt_template:
            messages = [self._build_system_message(self.settings.prompt_settings.prompt_template)]

        self._append_messages(messages, self.context_utterances)
        return messages

    def _build_chatml_turn(self, role: str, content: str) -> str:
        turn = f"<|im_start|>{role}\n{content}<|im_end|>\n"
        return turn

    def _convert_raw_prompt_to_str(self) -> str:
        prompt_str_parts = []
        for prompt in self.prompt_raw:
            prompt_str_parts.append(self._build_chatml_turn(role=prompt["role"], content=prompt["content"]))
        return "".join(prompt_str_parts)

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

    async def _build_raw_prompt(self, stop_before_utt_conv: UtteranceConversation | None = None) -> Any:
        idx_to_split_context_by = self._idx_to_split_context_by()
        if idx_to_split_context_by is None:
            idx_to_split_context_by = 0

        messages = [self._build_system_message(self.settings.prompt_settings.prompt_template[0])]
        self._append_messages(messages, self.context_utterances[:idx_to_split_context_by])
        messages.append(self._build_system_message(self.settings.prompt_settings.prompt_template[1]))
        self._append_messages(messages, self.context_utterances[idx_to_split_context_by:])
        return messages

    def _get_token_limit(self) -> int:
        token_limit = 3584 - self.settings.max_tokens  # minus maximum number of tokens for the response
        return token_limit

    def num_tokens_from_messages(self, messages: list[dict[str, str]], prime=True):
        """Returns the number of tokens used by a list of messages."""
        model = "gpt-3.5-turbo-0301"  # TODO oleksandr: accept model as a parameter ?
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            if prime:
                num_tokens += 2  # every reply is primed with <im_start>assistant
            # TODO oleksandr: why is num_tokens off by 1 compared to info from openai response?
            return num_tokens

        raise NotImplementedError(
            f"num_tokens_from_messages() is not presently implemented for model {model}. "
            f"See https://github.com/openai/openai-python/blob/main/chatml.md for information "
            f"on how messages are converted to tokens."
        )

    def _calculate_static_token_number(self) -> int:
        static_prompt = [
            {
                "content": self.settings.prompt_settings.prompt_template[0],
                "role": "system",
            },
            {
                "content": self.settings.prompt_settings.prompt_template[1],
                "role": "system",
            },
        ]
        static_token_num = self.num_tokens_from_messages(static_prompt, prime=True)
        return static_token_num

    def _calculate_utterance_token_number(self, role: str, content: str) -> int:
        token_num = self.num_tokens_from_messages(
            [
                {
                    "content": content,
                    "role": role,
                },
            ],
            prime=False,
        )
        return token_num

    # noinspection PyMethodMayBeStatic
    async def _prepare_context_utterances(
        self,
        conversation_id: int,
        stop_before_utt_conv: Utterance | None = None,
    ) -> list[Utterance]:
        conv_hard_limit = 1000
        token_limit = self._get_token_limit()
        self.estimated_prompt_token_number = self._calculate_static_token_number()
        token_number = self.estimated_prompt_token_number

        # TODO oleksandr: there is no point in descending order and eventual reversal of the list (get rid of both)
        utt_conv_objects = (
            UtteranceConversation.objects.filter(conversation_id=conversation_id)
            .select_related("utterance")
            .order_by("-utterance__arrival_timestamp_ms")
        )

        if stop_before_utt_conv:
            # pretend that the last utterance was the one before the stop_before_utterance
            utt_conv_objects = await sync_to_async(list)(utt_conv_objects)
            for idx, utt_conv_object in enumerate(utt_conv_objects):
                if utt_conv_object.id == stop_before_utt_conv.pk:
                    utt_conv_objects = utt_conv_objects[idx + 1 :]
                    break
            utt_conv_objects = utt_conv_objects[:conv_hard_limit]
        else:
            # don't pretend, just take the last conv_hard_limit utterances
            utt_conv_objects = utt_conv_objects[:conv_hard_limit]
            utt_conv_objects = await sync_to_async(list)(utt_conv_objects)

        utterances = []
        for utt_conv_object in utt_conv_objects:
            token_number += self._calculate_utterance_token_number(
                role="assistant" if utt_conv_object.utterance.is_bot else "user",
                content=utt_conv_object.utterance.text,
            )
            if token_number > token_limit:
                break
            self.estimated_prompt_token_number = token_number
            utterances.append(utt_conv_object.utterance)

        utterances.reverse()
        return utterances


class ChatGptEvenLaterPromptCompletion(ChatGptLatePromptCompletion):
    def _idx_to_split_context_by(self) -> int:
        last_user_utterance_index = super()._idx_to_split_context_by()
        if last_user_utterance_index is not None:
            last_user_utterance_index += 1
        return last_user_utterance_index
