# SPDX-License-Identifier: MIT
import asyncio
from io import StringIO
from unittest.mock import patch

import pytest

from odxtools.isotp_state_machine import IsoTpStateMachine


@pytest.mark.parametrize("payload_length", [1, 7, 8, 10, 14, 18, 22, 30, 46, 62])
@pytest.mark.parametrize("as_bytearray", [False, True])
def test_single_frame_lengths(payload_length: int, as_bytearray: bool) -> None:
    payload = bytes(range(payload_length))
    if payload_length <= 7:
        frame = bytes([payload_length]) + payload
        frame_length = 8
    else:
        frame = bytes([0, payload_length]) + payload
        frame_length = next(n for n in [12, 16, 20, 24, 32, 48, 64] if n >= len(frame))
    frame = frame.ljust(frame_length, b"\xcc")
    decoder = IsoTpStateMachine(0x123)
    data = bytearray(frame) if as_bytearray else frame

    with patch.object(decoder, "on_single_frame") as single, patch.object(
            decoder, "on_telegram_complete") as complete:
        assert list(decoder.decode_rx_frame(0x123, data)) == [(0x123, payload)]
        single.assert_called_once_with(0, payload)
        complete.assert_called_once_with(0, payload)


@pytest.mark.parametrize("frame_length", [8, 12, 16, 20, 24, 32, 48, 64])
@pytest.mark.parametrize("payload_length", [125, 4095, 4096, 65536])
def test_segmented_frame_lengths(frame_length: int, payload_length: int) -> None:
    payload = bytes(i % 256 for i in range(payload_length))
    if payload_length <= 4095:
        header = (0x1000 | payload_length).to_bytes(2, "big")
    else:
        header = b"\x10\x00" + payload_length.to_bytes(4, "big")
    first_payload_length = frame_length - len(header)
    first = header + payload[:first_payload_length]
    decoder = IsoTpStateMachine([0x123, 0x456])

    with patch.object(decoder, "on_first_frame") as on_first, patch.object(
            decoder, "on_telegram_complete") as complete, patch.object(
                decoder, "on_sequence_error") as sequence_error:
        assert list(decoder.decode_rx_frame(0x456, first)) == []
        assert decoder.telegram_data(1) == bytearray(payload[:first_payload_length])
        on_first.assert_called_once_with(1, first)
        result: list[tuple[int, bytes]] = []
        for index, offset in enumerate(range(first_payload_length, len(payload), frame_length - 1)):
            frame = bytes([0x20 | ((index + 1) % 16)]) + payload[offset:offset + frame_length - 1]
            result.extend(decoder.decode_rx_frame(0x456, frame.ljust(frame_length, b"\xcc")))
        assert result == [(0x456, payload)]
        complete.assert_called_once_with(1, payload)
        sequence_error.assert_not_called()
        assert decoder.telegram_data(0) is None


@pytest.mark.parametrize("format_name", ["normal", "log"])
def test_read_can_fd_single_frame(format_name: str) -> None:
    payload = bytes(range(62))
    frame = bytes([0, len(payload)]) + payload
    if format_name == "normal":
        line = "can0  123  [64] " + " ".join(f"{value:02X}" for value in frame)
    else:
        line = "(123.456) can0 123##1" + frame.hex()
    decoder = IsoTpStateMachine(0x123)

    async def read() -> list[tuple[int, bytes]]:
        return [telegram async for telegram in decoder.read_telegrams(StringIO(line + "\n"))]

    assert asyncio.run(read()) == [(0x123, payload)]


@pytest.mark.parametrize("payload_length", [1, 7])
@pytest.mark.parametrize("frame_length", [12, 64])
def test_short_payload_in_can_fd_single_frame(payload_length: int, frame_length: int) -> None:
    payload = bytes(range(payload_length))
    frame = (bytes([0, payload_length]) + payload).ljust(frame_length, b"\xcc")
    assert list(IsoTpStateMachine(0x123).decode_rx_frame(0x123, frame)) == [(0x123, payload)]


@pytest.mark.parametrize("length", [0, 11])
def test_invalid_can_fd_single_frame_length(length: int) -> None:
    frame = bytes([0, length]) + b"\xcc" * 10
    decoder = IsoTpStateMachine(0x123)
    with patch.object(decoder, "on_telegram_complete") as complete:
        with pytest.raises(ValueError, match="single frame escape length"):
            list(decoder.decode_rx_frame(0x123, frame))
        complete.assert_not_called()


@pytest.mark.parametrize("frame_length", [2, 3, 4, 5])
def test_incomplete_first_frame_escape_length(frame_length: int) -> None:
    decoder = IsoTpStateMachine(0x123)
    with pytest.raises(ValueError, match="first frame escape length"):
        list(decoder.decode_rx_frame(0x123, b"\x10\x00\x00\x01\x00"[:frame_length]))
    assert decoder.telegram_data(0) is None
