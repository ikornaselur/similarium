import re

import aiohttp

from similarium.config import config
from similarium.logging import logger

NON_BRACKET_USER_ID_REGEX = r"(?<!<)(?P<user_id>@[A-Z0-9]+)(?!>)"


def _fix_openai_response(content: str) -> str:
    """Fix common issues with the response form OpenAI

    These issues include:
        * Extra quotes around the response
        * Slack user tags are incorrect
    """
    # Remove extra quotes around the content
    if content[0] == content[-1] == '"':
        content = content[1:-1]

    # Format the slack user tags correctly
    # If the tag is in the form @ABCD1234 it needs to be in the form <@ABCD1234>
    # Use regex to find and replace the tags
    content = re.sub(NON_BRACKET_USER_ID_REGEX, r"<\1>", content)

    return content


async def chat_completion_request(prompt: str) -> str:
    """Make request to OpenAI Chat completion service and return the response"""
    logger.debug(f"Making request to OpenAI API: {prompt=}")

    api_url = config.openai.api_url
    headers = {"Authorization": f"Bearer {config.openai.api_key}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.openai.temperature,
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
    content = response["choices"][0]["message"]["content"]

    return _fix_openai_response(content)


def get_hint_prompt(secret: str, close_words: list[str]) -> str:
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
            "",
            (
                "Please write a hint (it has to be a sentence) to help find the secret"
                " word, without using any of the close words or using the secret itself"
            ),
            "Reply only with the hint and nothing else.",
        ]
    )


def get_overview_prompt(secret: str, context: list[str]) -> str:
    return "\n".join(
        [
            (
                "I am running a secret word guessing game. There is a single secret and"
                " players are able to make guesses to find the secret word. I want to"
                " write an overview of how the game went yesterday."
            ),
            f"The secret was '{secret}'.",
            *context,
            (
                "Reveal the secret and make a witty overview of how the"
                " game went yesterday. Incorporate the secret word somehow into the"
                " overview. Congratulate the winners. This overview is just for the"
                " players. Do not explain the rules of the game. Reply only with the"
                " overview and nothing else."
            ),
        ]
    )
