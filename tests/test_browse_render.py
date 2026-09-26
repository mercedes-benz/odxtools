# SPDX-License-Identifier: MIT
from typing import Any

import pytest

pytest.importorskip("prompt_toolkit")

from prompt_toolkit import Application
from prompt_toolkit.application import create_app_session
from prompt_toolkit.data_structures import Size
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from odxtools.cli import _browse_utils


class SmallTerminalOutput(DummyOutput):

    def get_size(self) -> Size:
        return Size(rows=12, columns=24)


def test_wrapped_question_and_scrolling_keep_selection_visible(monkeypatch: pytest.MonkeyPatch
                                                              ) -> None:
    question = "Select a diagnostic service from the available vehicle services."
    frames: list[list[str]] = []
    keys = iter(["\x1b[6~", "\x1b[F", "\r"])

    with create_pipe_input() as pipe, create_app_session(input=pipe, output=SmallTerminalOutput()):

        def capture_frame(app: Application[Any]) -> None:
            screen = app.renderer._last_screen
            if app.is_done or screen is None:
                return
            # Inspect actual rendered cells, then send one key per frame so that
            # paging and scrolling must produce a visible intermediate result.
            frames.append([
                "".join(screen.data_buffer[row][column].char
                        for column in range(24))
                for row in range(screen.height)
            ])
            pipe.send_text(next(keys, "\r"))

        def capturing_application(**kwargs: Any) -> Application[Any]:
            return Application(after_render=capture_frame, **kwargs)

        monkeypatch.setattr(_browse_utils, "Application", capturing_application)
        result = _browse_utils.prompt_questions([{
            "type": "list",
            "name": "service",
            "message": question,
            "choices": [f"service-{index:02}" for index in range(25)],
        }])

    assert result["service"] == "service-24"
    assert len(frames) == 3
    title_rows = next(index for index, row in enumerate(frames[0]) if row.startswith(">"))
    assert title_rows > 1
    assert "".join(frames[0][:title_rows]).rstrip() == f"? {question}"
    visible_choices = sum(row.lstrip().startswith(("> service-", "service-")) for row in frames[0])
    assert f"> service-{visible_choices:02}" in [row.rstrip() for row in frames[1]]
    assert "> service-24" in [row.rstrip() for row in frames[2]]
