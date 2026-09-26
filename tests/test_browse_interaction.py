# SPDX-License-Identifier: MIT
import sys
from types import SimpleNamespace

import pytest

pytest.importorskip("prompt_toolkit")

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from odxtools.cli.browse import browse
from odxtools.loadfile import load_pdx_file

DOWN = "\x1b[B"
LAST = "\x1b[F\r"


@pytest.mark.parametrize(
    "service_index, message_index, answers, payload",
    [
        # Reject invalid numeric input, then accept a hexadecimal integer.
        (0, 0, "\rbad\r\x150x12\r3\r", "ba1203"),
        # Leave the optional bribe blank and select its default value.
        (3, 0, "\r\r\r", "100000"),
        # Select the 'true' texttable value for a positive response.
        (3, 1, "\r" + DOWN + "\r", "5001"),
        # Declining the encoding question returns directly to the services.
        (0, 0, DOWN + "\r", None),
    ])
def test_browse_encode_and_navigate_back(monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str], service_index: int,
                                         message_index: int, answers: str,
                                         payload: str | None) -> None:
    database = load_pdx_file("./examples/somersault.pdx")
    monkeypatch.setattr(sys, "__stdin__", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    # Choose somersault_lazy, a service, and its request/response.
    keys = DOWN * 2 + "\r" + DOWN * service_index + "\r"
    keys += DOWN * message_index + "\r" + answers
    # Reopen a service and go back from its message menu, then back from
    # the service menu and exit. No prompt or encoding function is mocked.
    keys += "\r" + LAST * 3
    with create_pipe_input() as pipe, create_app_session(input=pipe, output=DummyOutput()):
        # An unexpected extra prompt fails instead of waiting for user input.
        pipe.send_text(keys + "\x03")
        try:
            browse(database)
        except KeyboardInterrupt:
            pytest.fail("The browser asked for more input than expected")

    output = capsys.readouterr().out
    assert "ECU-VARIANT 'somersault_lazy'" in output
    if payload is None:
        assert "Message payload:" not in output
    else:
        assert f"Message payload: 0x{payload}" in output
        assert output.count("Message payload:") == 1
