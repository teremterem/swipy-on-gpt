# pylint: disable=too-few-public-methods
import random

import openai

from swipy_config import MOCK_GPT


class GptCompletion:
    def __init__(self, prompt: str, temperature: float):
        self.prompt = prompt
        self.temperature = temperature
        self.completion: str | None = None

    async def fulfil(self) -> None:
        if MOCK_GPT:
            self.completion = f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"
        else:
            gpt_response = await openai.Completion.acreate(
                prompt=self.prompt,
                engine="text-davinci-003",
                temperature=self.temperature,
                max_tokens=512,
                # TODO oleksandr: stop=["\n", " Human:", " AI:"],
            )
            self.completion = gpt_response.choices[0].text
            assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"


class PaddedGptCompletion(GptCompletion):
    def __init__(self, prompt_content: str, prompt_template: str, temperature: float):
        prompt = prompt_template.format(prompt_content)
        super().__init__(prompt=prompt, temperature=temperature)


class DialogGptCompletion(PaddedGptCompletion):
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

        prompt_parts = []
        self.build_prompt_content(prompt_parts)
        prompt_parts.append(self.utterance_prefix(self.bot_name))
        prompt_content = "\n".join(prompt_parts)
        super().__init__(prompt_template=prompt_template, prompt_content=prompt_content, temperature=temperature)

        self.completion_before_strip: str | None = None

    def build_prompt_content(self, prompt_parts: list[str]) -> None:
        if self.previous_completion is not None:
            self.previous_completion.build_prompt_content(prompt_parts)
            if self.previous_completion.completion is not None:
                prompt_parts.append(
                    f"{self.utterance_prefix(self.previous_completion.bot_name)} {self.previous_completion.completion}"
                )

        if self.user_utterance is not None:
            prompt_parts.append(f"{self.utterance_prefix(self.user_name)} {self.user_utterance}")

    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}*:"

    async def fulfil(self) -> None:
        await super().fulfil()
        self.completion_before_strip = self.completion
        self.completion = self.completion.strip()


class DialogGptCompletionHistory:
    def __init__(self, user_name: str, bot_name: str, prompt_template: str = "{}", temperature: float = 1):
        self.user_name = user_name
        self.bot_name = bot_name
        self.prompt_template = prompt_template
        self.temperature = temperature

        self.completions: list[DialogGptCompletion] = []

    def new_user_utterance(self, user_utterance: str) -> DialogGptCompletion:
        gpt_completion = DialogGptCompletion(
            prompt_template=self.prompt_template,
            user_name=self.user_name,
            bot_name=self.bot_name,
            user_utterance=user_utterance,
            previous_completion=self.completions[-1] if self.completions else None,
            temperature=self.temperature,
        )
        self.completions.append(gpt_completion)
        return gpt_completion
