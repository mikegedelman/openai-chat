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

from rich.console import Console
from rich.markdown import Markdown



class ChatCLI:
    def __init__(self, *, api_key, cli_args):
        self.console = Console()
        self.api_key = api_key

        self.test_mode = cli_args.test
        if self.test_mode:
            self.model = "_testing_mode"

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
        print(f"Using {self.model}")

    def is_openai(self, modelname):
        if modelname.startswith("gpt") or modelname.startswith("o1"):
            return True
        
        return False

    def set_model(self, modelname):
        self.model = modelname

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
            case "backend?":
                self.display_backend()
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


    parser = argparse.ArgumentParser("chatgpt")
    parser.add_argument("--test", action="store_true", help="Run in test mode - won't send anything to the API")
    args = parser.parse_args()

    cli = ChatCLI(api_key=api_key, cli_args=args)
    cli.run()



if __name__ == "__main__":
    main()
