# SPDX-License-Identifier: MIT
from unittest.mock import Mock

import can
import pytest

from odxtools.isotp_state_machine import IsoTpActiveDecoder


@pytest.mark.parametrize("consecutive_frames", [254, 255, 256, 510, 511, 585])
@pytest.mark.parametrize("padding_size", [0, 8])
def test_flow_control_block_boundaries(consecutive_frames: int, padding_size: int) -> None:
    # A full first frame carries six bytes; each consecutive frame carries seven.
    payload_length = min(4095, 6 + 7 * consecutive_frames)
    payload = bytes(i % 256 for i in range(payload_length))
    bus = Mock(spec=can.BusABC)
    decoder = IsoTpActiveDecoder(bus, [0x123], [0x456], padding_size=padding_size)
    first = (0x1000 | len(payload)).to_bytes(2, "big") + payload[:6]
    assert list(decoder.decode_rx_frame(0x123, first)) == []
    assert bus.send.call_count == 1
    flow_control_at = [0]
    result: list[tuple[int, bytes]] = []
    for index, offset in enumerate(range(6, len(payload), 7), start=1):
        frame = bytes([0x20 | (index % 16)]) + payload[offset:offset + 7]
        previous_count = bus.send.call_count
        result.extend(decoder.decode_rx_frame(0x123, frame.ljust(8, b"\xaa")))
        if bus.send.call_count != previous_count:
            flow_control_at.append(index)

    # The sender waits after each advertised 255-CF block, unless already finished.
    assert flow_control_at == [0, *range(255, consecutive_frames, 255)]
    assert result == [(0x123, payload)]
    for call in bus.send.call_args_list:
        message = call.args[0]
        assert message.arbitration_id == 0x456
        assert not message.is_extended_id
        assert message.data == bytearray(b"\x30\xff\x00".ljust(padding_size, b"\xaa"))


def test_single_frame_needs_no_flow_control() -> None:
    bus = Mock(spec=can.BusABC)
    decoder = IsoTpActiveDecoder(bus, [0x123], [0x456])
    assert list(decoder.decode_rx_frame(0x123, b"\x03abc")) == [(0x123, b"abc")]
    bus.send.assert_not_called()
