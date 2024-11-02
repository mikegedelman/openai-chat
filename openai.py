import json
import os
import typing

import requests

import base

class OpenAIChatResponse(typing.NamedTuple):
    request_id: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIBackend(base.APIBackend):
    def __init__(self, test_mode: bool):
        self.test_mode = test_mode            

    def openai_completions_api(self, q: str, model: str):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environ must be set.")

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": q,
                }
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        response = r.json()

        try:
            return OpenAIChatResponse(
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

    def test_fake_response(self):
        return OpenAIChatResponse(
            request_id="fake-request-id",
            text="Hello! How can I assist you today?",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )