import json
import os
import readline
import sys
import typing

import requests
from rich.console import Console
from rich.markdown import Markdown


api_key = os.environ.get("OPENAI_API_KEY")

console = Console()


class ChatResponse(typing.NamedTuple):
    request_id: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def ask_gpt(q):
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": q,
            }
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        verify=False,
        headers=headers,
        json=payload,
    )
    r.raise_for_status()
    response = r.json()

    try:
        return ChatResponse(
            request_id=response["id"],
            text=response["choices"][0]["message"]["content"],
            prompt_tokens=response["usage"]["prompt_tokens"],
            completion_tokens=response["usage"]["completion_tokens"],
            total_tokens=response["usage"]["total_tokens"],
        )
    except:
        print("Error evaluating the response from OpenAI. Here's the raw payload:")
        print(json.dumps(response))
        raise


def main():
    if not api_key:
        print("OPENAI_API_KEY environ must be set.")
        sys.exit(-1)

    while True:
        try:
            question = console.input("> ")
            if not question:
                continue
        except KeyboardInterrupt:
            break  # Control-C pressed.
        except EOFError:
            break  # Control-D pressed.

        r = ask_gpt(question)
        console.print("\n")
        console.print(Markdown(r.text))
        console.print(
            f"\n({r.total_tokens} tokens used [{r.prompt_tokens} | {r.completion_tokens}]) (request id: {r.request_id})"
        )


if __name__ == "__main__":
    main()
