import random

import openai

from swipy_config import MOCK_GPT


class GptCompletion:  # pylint: disable=too-few-public-methods
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
