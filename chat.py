#!/usr/bin/env python3
import argparse
import json
import os
import sys
import typing
import enum
import tempfile
import subprocess

# readline module isn't available on windows
try:
    import readline
except ModuleNotFoundError:
    pass

import requests
from rich.console import Console
from rich.markdown import Markdown


class ChatGPTModel(enum.Enum):
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"
    gpt_35_turbo = "gpt-3.5-turbo"
    o1_preview = "o1-preview"
    o1_mini = "o1-mini"
    test_mode = "_test_mode"


class ChatResponse(typing.NamedTuple):
    request_id: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCLI:
    def __init__(self, *, api_key, cli_args):
        self.console = Console()
        self.api_key = api_key

        self.test_mode = cli_args.test
        if self.test_mode:
            self.model = ChatGPTModel.test_mode
        else:
            self.model = ChatGPTModel.gpt_4o


    def openai_completions_api(self, q):
        payload = {
            "model": self.model.value,
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

    def test_fake_response(self):
        return ChatResponse(
            request_id="fake-request-id",
            text="Hello! How can I assist you today?",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )

    def send_message(self, msg):
        self.console.rule("[bold]YOU[/bold]", style="cyan")
        self.console.print(Markdown(msg), style="cyan")
        self.console.rule("[bold]AI[/bold]", style="purple")
        if self.test_mode:
            r = self.test_fake_response()
        else:
            r = self.openai_completions_api(msg)
        self.console.print(Markdown(r.text))
        self.console.print(
            f"\n({r.total_tokens} tokens used [{r.prompt_tokens} | {r.completion_tokens}]) (request id: {r.request_id}) ",
            style="purple",
            end="",
        )
        self.console.print(
            self.model.value,
            style="purple",
            highlight=False,
        )

    def spawn_editor_and_send(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpfile = f"{tmpdir}/question.txt"
            result = subprocess.run(["vim", tmpfile])
            if result.returncode != 0:
                print("error: nonzero exit code from editor, not sending message")
                return

            with open(tmpfile) as f:
                msg = f.read()
                if len(msg):
                    self.send_message(msg) 

    def display_model(self):
        print(f"Using {self.model.value}")

    def display_all_models(self):
        print("Available models:")
        for m in ChatGPTModel:
            print(f"\t{m.value}")

    def set_model(self, modelname):
        try:
            self.model = ChatGPTModel(modelname)
        except ValueError:
            print(f"Unknown model: {modelname}")
            self.display_all_models()
        self.display_model()

    def handle_command(self, cmds):
        split = cmds.split(" ")
        cmd = split[0]
        match cmd:
            case "e":
                self.spawn_editor_and_send()
            case "model":
                self.set_model(split[1])
            case "model?":
                self.display_model()
            case "models?":
                self.display_all_models()
            case _:
                print(f"unrecognized command: {cmd}")
    
    def run(self):
        if self.test_mode:
            print("Test mode: messages will not be sent to the API")
        else:
            self.display_model()

        while True:
            try:
                question = input("> ")
                if not question:
                    continue
                if question.startswith("/"):
                    self.handle_command(question[1:])
                else:
                    self.send_message(question)
            except KeyboardInterrupt:
                break  # Control-C pressed.
            except EOFError:
                break  # Control-D pressed.


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY environ must be set.")
        sys.exit(-1)

    parser = argparse.ArgumentParser("chatgpt")
    parser.add_argument("--test", action="store_true", help="Run in test mode - won't send anything to the API")
    args = parser.parse_args()

    cli = ChatCLI(api_key=api_key, cli_args=args)
    cli.run()



if __name__ == "__main__":
    main()
