# pylint: disable=too-few-public-methods
import random
from typing import Collection

import openai

from swipy_config import MOCK_GPT


class GptCompletion:
    def __init__(self, prompt: str, temperature: float, stop_list: Collection[str]):
        self.prompt = prompt
        self.temperature = temperature
        self.completion: str | None = None
        self.stop_list = stop_list

    async def fulfil(self) -> None:
        if MOCK_GPT:
            # await asyncio.sleep(12)
            self.completion = f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"
        else:
            gpt_response = await openai.Completion.acreate(
                # TODO oleksandr: submit user id from Telegram (or from your database) too
                prompt=self.prompt,
                engine="text-davinci-003",
                temperature=self.temperature,
                max_tokens=512,
                stop=self.stop_list,
            )
            self.completion = gpt_response.choices[0].text
            assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"


class PaddedGptCompletion(GptCompletion):
    def __init__(self, prompt_content: str, prompt_template: str, temperature: float, stop_list: Collection[str]):
        prompt = prompt_template.format(prompt_content)
        super().__init__(prompt=prompt, temperature=temperature, stop_list=stop_list)


class DialogGptCompletion(PaddedGptCompletion):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        user_name: str,
        bot_name: str,
        user_utterance: str,
        prompt_template: str,
        temperature: float,
        previous_completion: "DialogGptCompletion" = None,
    ):
        self.user_name = user_name
        self.bot_name = bot_name
        self.user_utterance = user_utterance
        self.previous_completion = previous_completion

        self.user_prefix = self.utterance_prefix(self.user_name)
        self.bot_prefix = self.utterance_prefix(self.bot_name)

        prompt_parts = []
        self.build_prompt_content(prompt_parts)
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

    def build_prompt_content(self, prompt_parts: list[str]) -> None:
        if self.previous_completion is not None:
            self.previous_completion.build_prompt_content(prompt_parts)
            if self.previous_completion.completion is not None:
                prompt_parts.append(f"{self.bot_prefix} {self.previous_completion.completion}")

        if self.user_utterance is not None:
            prompt_parts.append(f"{self.user_prefix} {self.user_utterance}")

    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}*:"

    async def fulfil(self) -> None:
        await super().fulfil()
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
            prompt_template=self.prompt_template,
            user_name=user_name,
            bot_name=self.bot_name,
            user_utterance=user_utterance,
            previous_completion=self.completions[-1] if self.completions else None,
            temperature=self.temperature,
        )
        self.completions.append(gpt_completion)
        return gpt_completion

    def clear_history(self) -> None:
        self.completions = []

    def __str__(self) -> str:
        return f"{self.experiment_name} T={self.temperature:.1f}"
