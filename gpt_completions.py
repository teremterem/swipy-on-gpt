import random

import openai
from telegram import Update

from swipy_config import MOCK_GPT


class SimpleCompletionBase:
    def __init__(self, temperature: float = 1):
        self.temperature = temperature

    async def display_gpt_completion(self, update: Update) -> None:
        prompt = update.effective_message.text
        completion = await self.request_gpt_completion(prompt)
        answer = self.display_model_name() + prompt + completion
        await update.effective_chat.send_message(text=answer, parse_mode="Markdown")

    def display_model_name(self) -> str:
        return f"{self.__class__.__name__} **T={self.temperature}**\n\n"

    async def request_gpt_completion(self, prompt: str) -> str:
        if MOCK_GPT:
            return f"\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"

        gpt_response = await openai.Completion.acreate(
            prompt=prompt, engine="text-davinci-003", temperature=self.temperature, max_tokens=160
        )
        assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"

        return gpt_response.choices[0].text
