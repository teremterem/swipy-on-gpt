# pylint: disable=too-few-public-methods
import random

import openai

from swipy_config import MOCK_GPT


class GptCompletion:
    def __init__(self, prompt: str, temperature: float = 1):
        self.prompt = prompt
        self.temperature = temperature
        self.completion: str | None = None

    async def fulfil(self, prompt: str) -> str:
        if MOCK_GPT:
            self.completion = f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"
        else:
            gpt_response = await openai.Completion.acreate(
                prompt=prompt,
                engine="text-davinci-003",
                temperature=self.temperature,
                max_tokens=256,
                # TODO oleksandr: stop=["\n", " Human:", " AI:"],
            )
            assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
            self.completion = gpt_response.choices[0].text

        return self.completion


class PaddedGptCompletion(GptCompletion):
    def __init__(self, prompt_template: str, prompt_content: str, temperature: float = 1):
        prompt = prompt_template.format(prompt_content)
        super().__init__(prompt, temperature)


class DialogGptCompletion(PaddedGptCompletion):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        prompt_template: str,
        user_name: str,
        bot_name: str,
        user_utterance: str,
        previous_completion: "DialogGptCompletion" = None,
        temperature: float = 1,
    ):
        self.user_name = user_name
        self.bot_name = bot_name
        self.user_utterance = user_utterance
        self.previous_completion = previous_completion
        prompt_parts = []
        self.build_prompt_content(prompt_parts)
        prompt_parts.append(f"*{self.bot_name}*:")
        prompt_content = "\n".join(prompt_parts)
        super().__init__(prompt_template, prompt_content, temperature)

    def build_prompt_content(self, prompt_parts: list[str]) -> None:
        if self.previous_completion is not None:
            self.previous_completion.build_prompt_content(prompt_parts)
            if self.previous_completion.completion is not None:
                prompt_parts.append(f"*{self.previous_completion.bot_name}*: {self.previous_completion.completion}")

        if self.user_utterance is not None:
            prompt_parts.append(f"*{self.user_name}*: {self.user_utterance}")


class DialogGptCompletionHistory:
    def __init__(self, prompt_template: str, user_name: str, bot_name: str, temperature: float = 1):
        self.prompt_template = prompt_template
        self.user_name = user_name
        self.bot_name = bot_name
        self.temperature = temperature
        self.completions: list[DialogGptCompletion] = []

    def create(self, user_utterance: str) -> DialogGptCompletion:
        return DialogGptCompletion(
            prompt_template=self.prompt_template,
            user_name=self.user_name,
            bot_name=self.bot_name,
            user_utterance=user_utterance,
            previous_completion=self.completions[-1] if self.completions else None,
            temperature=self.temperature,
        )
