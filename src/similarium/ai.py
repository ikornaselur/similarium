import aiohttp
from similarium.config import config
from similarium.logging import logger


async def chat_completion_request(prompt: str) -> str:
    """Make request to OpenAI Chat completion service and return the response"""

    if not config.hints.enabled:
        logger.warning("Hints are not enabled")
        return "Hints are not enabled."

    logger.debug(f"Making request to OpenAI API: {prompt=}")

    api_url = config.hints.openai.api_url
    headers = {"Authorization": f"Bearer {config.hints.openai.api_key}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.hints.openai.temperature,
    }

    # Make async request to OpenAI API with aiohttp
    async with aiohttp.ClientSession() as client:
        async with client.post(api_url, headers=headers, json=data) as resp:
            response = await resp.json()

    if "error" in response:
        logger.error(f"OpenAI API error: {response=}")
        return (
            "Error occurred while making request to OpenAI API. (Note, this is not a"
            " hint)"
        )

    logger.debug(f"OpenAI API response: {response=}")
    return response["choices"][0]["message"]["content"]


def get_prompt(secret: str, close_words: list[str]) -> str:
    joined_words = ", ".join(close_words)

    return "\n".join(
        [
            "I am running a secret word guessing game.",
            (
                "There is a single secret and players are able to make guesses to find"
                " the secret word. Here are words that are similar or likely to be"
                f" used close to the secret word in news articles: {joined_words}"
            ),
            f"The secret word is '{secret}'",
            f"The top closest words to the secret are: {joined_words}",
            "",
            (
                "Please write a hint (it has to be a sentence) to help find the secret"
                " word, without using any of the close words or using the secret itself"
            ),
            "Reply only with the hint and nothing else.",
        ]
    )
