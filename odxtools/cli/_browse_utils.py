# SPDX-License-Identifier: MIT
from collections.abc import Callable
from typing import Any, TypedDict

from prompt_toolkit import Application, print_formatted_text
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.validation import Validator


class _BaseQuestion(TypedDict):
    type: str
    name: str
    message: str


class _Question(_BaseQuestion, total=False):
    choices: list[Any]
    default: Any
    validate: Callable[[Any], bool]
    filter: Callable[[Any], Any]


def _select(question: _Question) -> Any:
    # Keep values separate from labels: a choice can be an ODX object or None.
    choices = [c if isinstance(c, dict) else {"name": c, "value": c} for c in question["choices"]]
    if not choices:
        raise ValueError("A selection needs at least one choice")
    index = 0
    for i, c in enumerate(choices):
        if c["value"] == question.get("default"):
            index = i
    error = ""
    keys = KeyBindings()

    def fragments() -> StyleAndTextTuples:
        result: StyleAndTextTuples = []
        for i, c in enumerate(choices):
            if i == index:
                result.append(("[SetCursorPosition]", ""))
            result.append(
                ("reverse" if i == index else "", f"{'>' if i == index else ' '} {c['name']}"))
            if i < len(choices) - 1:
                result.append(("", "\n"))
        return result

    menu = Window(
        FormattedTextControl(fragments, focusable=True),
        height=Dimension(min=1, max=10),
        wrap_lines=True)

    @keys.add("c-p")
    @keys.add("s-tab")
    @keys.add("up")
    @keys.add("c-n")
    @keys.add("tab")
    @keys.add("down")
    @keys.add("pageup")
    @keys.add("pagedown")
    @keys.add("home")
    @keys.add("end")
    def move(event: KeyPressEvent) -> None:
        nonlocal index, error
        key = event.key_sequence[-1].key
        key = {"c-p": "up", "s-tab": "up", "c-n": "down", "c-i": "down"}.get(key, key)
        page = menu.render_info.window_height if menu.render_info else 10
        index = max(
            0,
            min(
                len(choices) - 1, {
                    "up": (index - 1) % len(choices),
                    "down": (index + 1) % len(choices),
                    "pageup": index - page,
                    "pagedown": index + page,
                    "home": 0,
                    "end": len(choices) - 1,
                }[key]))
        error = ""

    @keys.add("enter")
    def accept(event: KeyPressEvent) -> None:
        nonlocal error
        value = choices[index]["value"]
        if "validate" in question and not question["validate"](value):
            error = "Invalid input"
            return
        event.app.exit(result=value)

    @keys.add("c-c")
    def cancel(event: KeyPressEvent) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    app: Application[Any] = Application(
        layout=Layout(
            HSplit([
                Window(
                    FormattedTextControl(f"? {question['message']}"),
                    dont_extend_height=True,
                    wrap_lines=True),
                menu,
                Window(FormattedTextControl(lambda: error), height=lambda: 1 if error else 0),
            ]),
            focused_element=menu),
        key_bindings=keys,
        erase_when_done=True,
    )
    value = app.run()
    print_formatted_text(f"? {question['message']} {choices[index]['name']}")
    return value


def prompt_questions(questions: list[_Question]) -> dict[str, Any]:
    """Ask the browser's selection and text questions using prompt_toolkit."""
    answers = {}
    for question in questions:
        if question["type"] == "list":
            value = _select(question)
        elif question["type"] == "input":
            validator = None
            if "validate" in question:
                validator = Validator.from_callable(
                    question["validate"], error_message="Invalid input", move_cursor_to_end=True)
            value = prompt(
                f"? {question['message']} ", validator=validator, validate_while_typing=False)
        else:
            raise ValueError(f"Unsupported question type: {question['type']}")
        if "filter" in question:
            value = question["filter"](value)
        answers[question["name"]] = value
    return answers
