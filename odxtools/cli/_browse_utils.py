# SPDX-License-Identifier: MIT
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from prompt_toolkit import Application, print_formatted_text
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.validation import Validator


@dataclass
class SelectQuestion:
    message: str
    choices: Sequence[object]
    default: object | None = None
    validate: Callable[[object], bool] | None = None


@dataclass
class InputQuestion:
    message: str
    validate: Callable[[str], bool] | None = None
    filter: Callable[[str], object] | None = None


def _choice_parts(choice: object) -> tuple[str, object]:
    if isinstance(choice, Mapping):
        name = choice.get("name")
        if not isinstance(name, str):
            raise TypeError("Choice mappings need a string 'name'")
        return name, choice.get("value")
    return str(choice), choice


def _select(question: SelectQuestion) -> object:
    # Keep values separate from labels: a choice can be an ODX object or None.
    choices = [_choice_parts(choice) for choice in question.choices]
    if not choices:
        raise ValueError("A selection needs at least one choice")

    index = 0
    for i, (_, value) in enumerate(choices):
        if value == question.default:
            index = i

    error = ""
    keys = KeyBindings()

    def fragments() -> StyleAndTextTuples:
        result: StyleAndTextTuples = []
        for i, (name, _) in enumerate(choices):
            if i == index:
                result.append(("[SetCursorPosition]", ""))
            result.append(("reverse" if i == index else "", f"{'>' if i == index else ' '} {name}"))
            if i < len(choices) - 1:
                result.append(("", "\n"))
        return result

    menu = Window(
        FormattedTextControl(fragments, focusable=True),
        height=Dimension(min=1, max=10),
        wrap_lines=True,
    )

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
                len(choices) - 1,
                {
                    "up": (index - 1) % len(choices),
                    "down": (index + 1) % len(choices),
                    "pageup": index - page,
                    "pagedown": index + page,
                    "home": 0,
                    "end": len(choices) - 1,
                }[key],
            ),
        )
        error = ""

    @keys.add("enter")
    def accept(event: KeyPressEvent) -> None:
        nonlocal error
        value = choices[index][1]
        if question.validate is not None and not question.validate(value):
            error = "Invalid input"
            return
        event.app.exit(result=value)

    @keys.add("c-c")
    def cancel(event: KeyPressEvent) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    app: Application[object] = Application(
        layout=Layout(
            HSplit([
                Window(
                    FormattedTextControl(f"? {question.message}"),
                    dont_extend_height=True,
                    wrap_lines=True,
                ),
                menu,
                Window(FormattedTextControl(lambda: error), height=lambda: 1 if error else 0),
            ]),
            focused_element=menu,
        ),
        key_bindings=keys,
        erase_when_done=True,
    )
    value = app.run()
    print_formatted_text(f"? {question.message} {choices[index][0]}")
    return value


def prompt_question(question: SelectQuestion | InputQuestion) -> object:
    """Ask one browser selection or text question using prompt_toolkit."""
    if isinstance(question, SelectQuestion):
        return _select(question)

    validator = None
    if question.validate is not None:
        validator = Validator.from_callable(
            question.validate,
            error_message="Invalid input",
            move_cursor_to_end=True,
        )
    value = prompt(
        f"? {question.message} ",
        validator=validator,
        validate_while_typing=False,
    )
    if question.filter is not None:
        return question.filter(value)
    return value
