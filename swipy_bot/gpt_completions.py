import asyncio
import random
import traceback
from datetime import datetime

import openai
from asgiref.sync import sync_to_async

from swipy_app.models import GptCompletion, TelegramUpdate, Utterance
from swipy_bot.swipy_config import MOCK_GPT, MAX_CONVERSATION_LENGTH


class DialogGptCompletion:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        user_name: str,
        bot_name: str,
        user_utterance: str,
        prompt_template: str,
        temperature: float,
        chat_telegram_id: int,
    ):
        self.user_name = user_name
        self.bot_name = bot_name
        self.user_utterance = user_utterance

        self.user_prefix = self.utterance_prefix(self.user_name)
        self.bot_prefix = self.utterance_prefix(self.bot_name)

        self.prompt_template = prompt_template
        self.chat_telegram_id = chat_telegram_id
        self.temperature = temperature
        self.gpt_completion_in_db: GptCompletion | None = None
        self.stop_list = [
            # "\n",  # TODO oleksandr: enable this if it's the very first exchange ?
            self.user_prefix,
            # self.bot_prefix,
        ]

        self.completion: str | None = None
        self.prompt: str | None = None

    def utterance_prefix(self, utterer_name) -> str:
        return f"*{utterer_name}:*"

    async def build_prompt(self) -> bool:
        prompt_parts = []

        utterances = Utterance.objects.filter(chat_telegram_id=self.chat_telegram_id).order_by("-arrival_timestamp_ms")
        utterances = utterances[:MAX_CONVERSATION_LENGTH]
        utterances = await sync_to_async(list)(utterances)

        for idx, utterance in enumerate(utterances):
            if utterance.is_end_of_conv:
                # if the user sent /start ("Reset the dialog") at some point (or the conversation was restarted some
                # other way) then don't include any utterances before that into the context
                utterances = utterances[:idx]
                break

        has_history = len(utterances) > 0

        for utterance in reversed(utterances):
            prompt_parts.append(f"{self.utterance_prefix(utterance.name)} {utterance.text}")

        prompt_parts.append(self.bot_prefix)

        prompt_content = "\n".join(prompt_parts)
        self.prompt = self.prompt_template.format(DIALOG=prompt_content, USER=self.user_name)

        return has_history

    async def fulfil(self, tg_update_in_db: TelegramUpdate) -> None:
        has_history = await self.build_prompt()
        # temperature 1 should make conversation starters more "natural" (hopefully)
        temperature = self.temperature if has_history else 1.0  # TODO oleksandr: are you sure ?

        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        request_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        self.gpt_completion_in_db = await sync_to_async(GptCompletion.objects.create)(
            request_timestamp_ms=request_timestamp_ms,
            triggering_update=tg_update_in_db,
            chat_telegram_id=tg_update_in_db.chat_telegram_id,
            prompt=self.prompt,
            temperature=temperature,
        )
        await sync_to_async(self.gpt_completion_in_db.save)()

        try:
            if MOCK_GPT:
                await asyncio.sleep(2)
                self.completion = f"\n\nhErE gOeS gPt ReSpOnSe  (iT's a mOCK!) {random.randint(0, 1000000)}"
            else:
                gpt_response = await openai.Completion.acreate(
                    # TODO oleksandr: submit user id from Telegram (or from your database) too
                    prompt=self.prompt,
                    engine="text-davinci-003",
                    temperature=temperature,
                    max_tokens=512,
                    stop=self.stop_list,
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
            await sync_to_async(self.gpt_completion_in_db.save)()
            raise

        # TODO oleksandr: move this to some sort of utils.py ? or maybe to the model itself ?
        arrival_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
        self.gpt_completion_in_db.arrival_timestamp_ms = arrival_timestamp_ms
        self.gpt_completion_in_db.completion = self.completion
        await sync_to_async(self.gpt_completion_in_db.save)()


class DialogGptCompletionHistory:
    def __init__(self, bot_name: str, experiment_name, prompt_template: str = "{}", temperature: float = 1):
        self.bot_name = bot_name
        self.experiment_name = experiment_name
        self.prompt_template = prompt_template
        self.temperature = temperature

    def new_user_utterance(self, user_name: str, user_utterance: str, chat_telegram_id: int) -> DialogGptCompletion:
        gpt_completion = DialogGptCompletion(
            prompt_template=self.prompt_template,
            user_name=user_name,
            bot_name=self.bot_name,
            user_utterance=user_utterance,
            temperature=self.temperature,
            chat_telegram_id=chat_telegram_id,
        )
        return gpt_completion

    async def clear_history(self) -> None:
        # TODO oleksandr: implement this
        pass

    def __str__(self) -> str:
        return f"{self.experiment_name} T={self.temperature:.1f}"
