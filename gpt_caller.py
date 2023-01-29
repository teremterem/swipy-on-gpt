import openai


async def perform_gpt_completion(prompt: str) -> str:
    # TODO oleksandr: replace with "text-davinci-003"
    gpt_response = await openai.Completion.acreate(prompt=prompt, engine="text-ada-001")
    assert len(gpt_response.choices) == 1, f"Expected only one gpt choice, but got {len(gpt_response.choices)}"
    return prompt + gpt_response.choices[0].text
