import random
from datetime import datetime
from typing import Collection

import openai
from asgiref.sync import sync_to_async

from swipy_app.models import GptCompletion, TelegramUpdate
from swipy_bot.swipy_config import MOCK_GPT


class GptCompletionBase:
    def __init__(self, prompt: str, temperature: float, stop_list: Collection[str]):
        # pylint: disable=import-outside-toplevel

        self.prompt = prompt
        self.temperature = temperature
        self.completion: str | None = None
        self.gpt_completion_in_db: GptCompletion | None = None
        self.stop_list = stop_list

    async def fulfil(self, tg_update_in_db: TelegramUpdate) -> None:
        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        request_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        if MOCK_GPT:
            # await asyncio.sleep(12)
            self.completion = f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"
        else:
            gpt_response = await openai.Completion.acreate(
                # TODO oleksandr: submit user id from Telegram (or from your database) too
                prompt=self.prompt,  # TODO oleksandr: save prompt to the database too (and completion as well ?)
                engine="text-davinci-003",
                temperature=self.temperature,
                max_tokens=512,
                stop=self.stop_list,
            )
            self.completion = gpt_response.choices[0].text
            assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"

        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        self.gpt_completion_in_db = await sync_to_async(GptCompletion.objects.create)(
            request_timestamp_ms=request_timestamp_ms,
            arrival_timestamp_ms=arrival_timestamp_ms,
            triggering_update=tg_update_in_db,
            chat_telegram_id=tg_update_in_db.chat_telegram_id,
            prompt=self.prompt,
            completion=self.completion,
        )
        await sync_to_async(self.gpt_completion_in_db.save)()


class PaddedGptCompletion(GptCompletionBase):
    def __init__(self, prompt_content: str, prompt_template: str, temperature: float, stop_list: Collection[str]):
        prompt = prompt_template.format(prompt_content)
        super().__init__(prompt=prompt, temperature=temperature, stop_list=stop_list)


class DialogGptCompletion(PaddedGptCompletion):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        history: "DialogGptCompletionHistory",
        user_name: str,
        bot_name: str,
        user_utterance: str,
        prompt_template: str,
        temperature: float,
    ):
        self.user_name = user_name
        self.bot_name = bot_name
        self.user_utterance = user_utterance

        self.user_prefix = self.utterance_prefix(self.user_name)
        self.bot_prefix = self.utterance_prefix(self.bot_name)

        prompt_parts = []
        history.build_prompt_content(prompt_parts, self)
        prompt_parts.append(self.bot_prefix)
        prompt_content = "\n".join(prompt_parts)
        super().__init__(
            prompt_template=prompt_template,
            prompt_content=prompt_content,
            temperature=temperature,
            stop_list=[
                # "\n",  # TODO oleksandr: enable this if it's the very first exchange ?
                self.user_prefix,
                # self.bot_prefix,
            ],
        )

        self.completion_before_strip: str | None = None

    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}*:"

    async def fulfil(self, tg_update_in_db: TelegramUpdate) -> None:
        await super().fulfil(tg_update_in_db)
        self.completion_before_strip = self.completion
        self.completion = self.completion.strip()


class DialogGptCompletionHistory:
    def __init__(self, bot_name: str, experiment_name, prompt_template: str = "{}", temperature: float = 1):
        self.bot_name = bot_name
        self.experiment_name = experiment_name
        self.prompt_template = prompt_template
        self.temperature = temperature

        self.completions: list[DialogGptCompletion] = []

    def new_user_utterance(self, user_name: str, user_utterance: str) -> DialogGptCompletion:
        gpt_completion = DialogGptCompletion(
            history=self,
            prompt_template=self.prompt_template,
            user_name=user_name,
            bot_name=self.bot_name,
            user_utterance=user_utterance,
            temperature=self.temperature,
        )

        self.completions.append(gpt_completion)
        return gpt_completion

    def clear_history(self) -> None:
        self.completions = []

    def build_prompt_content(self, prompt_parts: list[str], current_completion: DialogGptCompletion) -> None:
        # TODO oleksandr: reimplement this to use DB
        # TODO oleksandr: make sure to only read the current user's history
        for completion in self.completions:
            if completion.user_utterance is not None:
                prompt_parts.append(f"{completion.user_prefix} {completion.user_utterance}")
            if completion.completion is not None:
                prompt_parts.append(f"{completion.bot_prefix} {completion.completion}")
        if current_completion.user_utterance is not None:
            prompt_parts.append(f"{current_completion.user_prefix} {current_completion.user_utterance}")

    def __str__(self) -> str:
        return f"{self.experiment_name} T={self.temperature:.1f}"
