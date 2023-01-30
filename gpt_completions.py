import itertools
import random

import openai
from telegram import Update
from telegram.constants import ParseMode

from swipy_config import MOCK_GPT


class SimpleGptCompletion:
    def __init__(self, temperature: float = 1):
        self.temperature = temperature

    def create_prompt(self, update: Update) -> str:
        return update.effective_message.text

    async def display_gpt_completion(self, update: Update) -> None:
        prompt = self.create_prompt(update)
        completion = await self.request_gpt_completion(prompt, update)
        message = f"==== {self.display_model_name()} ====\n\n{prompt}{completion}"
        await update.effective_chat.send_message(text=message, parse_mode=ParseMode.MARKDOWN)

    def display_model_name(self) -> str:
        return f"{self.__class__.__name__} T={self.temperature}"

    async def request_gpt_completion(self, prompt: str, update: Update) -> str:  # pylint: disable=unused-argument
        if MOCK_GPT:
            return f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"

        await update.effective_chat.send_message(text=prompt)
        gpt_response = await openai.Completion.acreate(
            prompt=prompt,
            engine="text-davinci-003",
            temperature=self.temperature,
            max_tokens=256,
            # TODO oleksandr: stop=["\n", " Human:", " AI:"],
        )
        assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
        response_text = gpt_response.choices[0].text
        await update.effective_chat.send_message(text=repr(response_text))

        return gpt_response.choices[0].text


class DialogGptCompletion(SimpleGptCompletion):
    def __init__(self, temperature: float = 1):
        super().__init__(temperature=temperature)
        self.dialog_history = []

    def create_prompt(self, update: Update) -> str:
        self.dialog_history.append(" ".join([self.create_user_name(update), update.effective_message.text]))
        prompt = "\n".join(itertools.chain(self.dialog_history, [self.create_bot_name()]))
        return prompt

    def create_user_name(self, update: Update) -> str:
        return f" *{update.effective_user.first_name}:*"

    def create_bot_name(self) -> str:
        return " *Swipy:*"

    async def request_gpt_completion(self, prompt: str, update: Update) -> str:
        completion = await super().request_gpt_completion(prompt, update)
        completion = completion.strip()
        self.dialog_history.append(" ".join([self.create_bot_name(), completion.strip()]))
        return " " + completion
