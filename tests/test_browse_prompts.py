# SPDX-License-Identifier: MIT
from typing import Any

import pytest

pytest.importorskip("prompt_toolkit")

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from odxtools.cli._browse_utils import prompt_questions
from odxtools.cli.dummy_sub_parser import DummyTool


def ask(question: dict[str, Any], keys: str) -> Any:
    # Exercise the real terminal parser and event loop without a physical TTY.
    with create_pipe_input() as pipe, create_app_session(input=pipe, output=DummyOutput()):
        pipe.send_text(keys)
        return prompt_questions([{"name": "answer", "message": "Choose", **question}])["answer"]


@pytest.mark.parametrize("keys, expected", [
    ("\r", 0),
    ("\x1b[B\r", 1),
    ("\x0e\r", 1),
    ("\x10\r", 24),
    ("\t\r", 1),
    ("\x1b[Z\r", 24),
    ("\x1b[A\r", 24),
    ("\x1b[F\r", 24),
    ("\x1b[F\x1b[B\r", 0),
    ("\x1b[F\x1b[H\r", 0),
    ("\x1b[6~\r", 10),
    ("\x1b[F\x1b[5~\r", 14),
    ("\x1b[5~\r", 0),
    ("\x1b[F\x1b[6~\r", 24),
])
def test_navigation(keys: str, expected: int) -> None:
    assert ask({"type": "list", "choices": list(range(25))}, keys) == expected


def test_objects_defaults_and_none() -> None:
    first, second = object(), object()
    question = {
        "type":
            "list",
        "choices": [
            {
                "name": "first",
                "value": first
            },
            {
                "name": "second",
                "value": second
            },
            {
                "name": "[none]",
                "value": None
            },
        ]
    }
    assert ask(question, "\r") is None
    assert ask({**question, "default": first}, "\r") is first
    assert ask({**question, "default": second}, "\r") is second
    assert ask(question, "\x1b[F\r") is None


def test_list_validation() -> None:
    assert ask(
        {
            "type": "list",
            "choices": ["invalid", "valid"],
            "validate": lambda value: value == "valid"
        }, "\r\x1b[B\r") == "valid"


def test_input_validation_before_conversion() -> None:
    assert ask({
        "type": "input",
        "validate": str.isdigit,
        "filter": int
    }, "bad\r\x15" + "42\r") == 42


def test_empty_input_and_byte_conversion() -> None:
    assert ask({"type": "input"}, "\r") == ""
    assert ask({"type": "input", "filter": bytes.fromhex}, "12 3B 05\r") == b"\x12\x3b\x05"


@pytest.mark.parametrize("kind", ["list", "input"])
def test_interrupt(kind: str) -> None:
    with pytest.raises(KeyboardInterrupt):
        ask({"type": kind, "choices": ["a", "b"]}, "\x03")


def test_empty_choices() -> None:
    with pytest.raises(ValueError, match="at least one"):
        ask({"type": "list", "choices": []}, "")


def test_missing_optional_dependency_hint() -> None:
    error = ModuleNotFoundError(name="prompt_toolkit")
    assert 'pip install "odxtools[browse-tool]"' in DummyTool("browse", error)._format_error()
