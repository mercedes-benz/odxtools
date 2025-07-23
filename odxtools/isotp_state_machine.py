#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import asyncio
import re
import sys
from collections.abc import AsyncGenerator, Iterable
from enum import IntEnum
from io import TextIOBase
from typing import TextIO

import bitstruct
import can


class IsoTp(IntEnum):
    # Frame types
    FRAME_TYPE_SINGLE = 0
    FRAME_TYPE_FIRST = 1
    FRAME_TYPE_CONSECUTIVE = 2
    FRAME_TYPE_FLOW_CONTROL = 3

    # Flow control flag values
    FLOW_CONTROL_CONTINUE = 0
    FLOW_CONTROL_WAIT = 1
    FLOW_CONTROL_ABORT = 2


class IsoTpStateMachine:
    can_normal_frame_re = re.compile(
        "([a-zA-Z0-9_-]*) *([0-9A-Fa-f ]*) *\\[[0-9]+\\] *([ 0-9A-Fa-f]+)")
    can_log_frame_re = re.compile("\\([0-9.]*\\) *([a-zA-Z0-9_-]*) ([0-9A-Fa-f]+)#([0-9A-Fa-f]+)")
    can_fd_log_frame_re = re.compile(
        "\\([0-9.]*\\) *([a-zA-Z0-9_-]*) ([0-9A-Fa-f]+)##[0-9A-Fa-f]([0-9A-Fa-f]+)")

    def __init__(self, can_rx_ids: int | list[int]):
        if isinstance(can_rx_ids, int):
            can_rx_ids = [can_rx_ids]

        self._can_rx_ids = can_rx_ids
        assert isinstance(self._can_rx_ids, list)

        self._telegram_specified_len = [0] * len(can_rx_ids)
        self._telegram_data: list[bytearray | None] = [None] * len(can_rx_ids)
        self._telegram_last_rx_fragment_idx = [0] * len(can_rx_ids)

    def decode_rx_frame(self, rx_id: int, data: bytes | bytearray) -> Iterable[tuple[int, bytes]]:
        """Handle the ISO-TP state transitions caused by a CAN frame.

        E.g., add some data to a telegram, etc. Returns a generator of
        (receive_id, payload_data) tuples.
        """
        try:
            telegram_idx = self._can_rx_ids.index(rx_id)
        except ValueError:
            return  # unknown CAN ID

        # decode the isotp segment
        frame_type, _ = bitstruct.unpack("u4u4", data)
        assert isinstance(frame_type, int)

        telegram_len = None
        if frame_type == IsoTp.FRAME_TYPE_SINGLE:
            frame_type, telegram_len = bitstruct.unpack("u4u4", data)
            assert isinstance(telegram_len, int)

            self.on_single_frame(telegram_idx, data[1:1 + telegram_len])
            self.on_telegram_complete(telegram_idx, data[1:1 + telegram_len])

            yield (rx_id, bytes(data[1:1 + telegram_len]))

        elif frame_type == IsoTp.FRAME_TYPE_FIRST:
            frame_type, telegram_len = bitstruct.unpack("u4u12", data)
            assert isinstance(telegram_len, int)

            self._telegram_specified_len[telegram_idx] = telegram_len
            self._telegram_data[telegram_idx] = bytearray(data[2:])
            self._telegram_last_rx_fragment_idx[telegram_idx] = 0

            self.on_first_frame(telegram_idx, data)

        elif frame_type == IsoTp.FRAME_TYPE_CONSECUTIVE:
            frame_type, rx_segment_idx = bitstruct.unpack("u4u4", data)
            assert isinstance(rx_segment_idx, int)

            expected_segment_idx = (self._telegram_last_rx_fragment_idx[telegram_idx] + 1) % 16
            telegram_data = self._telegram_data[telegram_idx]
            assert isinstance(telegram_data, bytearray)

            n = -1
            if expected_segment_idx == rx_segment_idx:
                self._telegram_last_rx_fragment_idx[telegram_idx] = rx_segment_idx
                telegram_data += data[1:]

                n = self._telegram_specified_len[telegram_idx]
                if len(telegram_data) > n:
                    # can frames can include padding, i.e. the length
                    # of the telegram payload is not necessarily a
                    # multiple of the segment payloads
                    telegram_data = telegram_data[:n]

            self.on_consecutive_frame(telegram_idx, rx_segment_idx, data[1:])

            if expected_segment_idx != rx_segment_idx:
                self.on_sequence_error(telegram_idx, expected_segment_idx, rx_segment_idx)
            elif len(telegram_data) == n:
                self.on_telegram_complete(telegram_idx, telegram_data)
                yield (rx_id, bytes(telegram_data))

        elif frame_type == IsoTp.FRAME_TYPE_FLOW_CONTROL:
            frame_type, flow_control_flag = bitstruct.unpack("u4u4", data)
            assert isinstance(flow_control_flag, int)

            self.on_flow_control_frame(telegram_idx, flow_control_flag)
        else:
            self.on_frame_type_error(telegram_idx, frame_type)

    async def read_telegrams(self,
                             bus: can.BusABC | TextIO) -> AsyncGenerator[tuple[int, bytes], None]:
        """This is equivalent to the :py:meth:`file.readlines()` method, but
        it yields ISO-TP telegrams instead of lines.

        The  yielded telegrams are (can_id, payload_data) tuples.

        :param bus: Input file or socket of can bus to read the can frames
        """

        if isinstance(bus, can.BusABC):
            # create an "on receive" event for the can bus
            rx_event = asyncio.Event()
            loop = asyncio.get_running_loop()
            loop.add_reader(bus, rx_event.set)

            while True:
                await rx_event.wait()

                msg = bus.recv()
                if msg is None:
                    continue
                for tmp in self.decode_rx_frame(msg.arbitration_id, msg.data):
                    yield tmp
        else:
            assert isinstance(bus, TextIOBase)
            # input is a file
            while bus:
                cur_line = bus.readline()
                if cur_line == "":
                    return

                if m := self.can_normal_frame_re.match(cur_line.strip()):
                    # frame_interface = m.group(1)
                    frame_id = int(m.group(2), 16)

                    frame_data_formatted = m.group(3).strip()
                    frame_data = bytearray([int(x, 16) for x in frame_data_formatted.split(" ")])

                    for tmp in self.decode_rx_frame(frame_id, frame_data):
                        yield tmp

                elif (m := self.can_log_frame_re.match(
                        cur_line.strip())) or (m := self.can_fd_log_frame_re.match(
                            cur_line.strip())):
                    # frame_interface = m.group(2)
                    frame_id = int(m.group(2), 16)

                    frame_data_formatted = m.group(3).strip()
                    frame_data_list = [
                        frame_data_formatted[i:i + 2]
                        for i in range(0, len(frame_data_formatted), 2)
                    ]
                    frame_data = bytearray([int(x, 16) for x in frame_data_list])

                    for tmp in self.decode_rx_frame(frame_id, frame_data):
                        yield tmp

                else:
                    print(
                        f"Warning: unrecognized frame format: '{cur_line.strip()}'",
                        file=sys.stderr)

    def can_rx_id(self, telegram_idx: int) -> int:
        """Given a Telegram index, returns the CAN ID for receiving data.

        :raises IndexError: The telegram index is invalid.
        """
        return self._can_rx_ids[telegram_idx]

    def telegram_data(self, telegram_idx: int) -> bytearray | None:
        """Given a Telegram index, returns the data received for this telegram
        so far.

        :raises IndexError: The telegram index is invalid.
        """
        return self._telegram_data[telegram_idx]

    ##############
    # Callbacks
    ##############
    def on_single_frame(self, telegram_idx: int, frame_payload: bytes | bytearray) -> None:
        """Callback method for when an ISO-TP message of type "single frame" has been received"""
        pass

    def on_first_frame(self, telegram_idx: int, frame_payload: bytes | bytearray) -> None:
        """Callback method for when an ISO-TP message of type "first frame" has been received"""
        pass

    def on_consecutive_frame(self, telegram_idx: int, segment_idx: int,
                             frame_payload: bytes | bytearray) -> None:
        """Callback method for when an ISO-TP message of type "consecutive frame" has been received"""
        pass

    def on_flow_control_frame(self, telegram_idx: int, flow_control_flag: int) -> None:
        """Method called when an ISO-TP message of type "flow control frame" has been received"""
        pass

    def on_sequence_error(self, telegram_idx: int, expected_idx: int, rx_idx: int) -> None:
        """Method called when a frame with an unexpected sequence index has been received"""
        pass

    def on_frame_type_error(self, telegram_idx: int, frame_type: int) -> None:
        """Method called when a frame exhibiting an unknown frame type has been received"""
        pass

    def on_telegram_complete(self, telegram_idx: int, telegram_payload: bytes | bytearray) -> None:
        """Method called when an ISO-TP telegram has been fully received"""
        pass


class IsoTpActiveDecoder(IsoTpStateMachine):
    """This class is equivalent to IsoTpStateMachine, but it sends out
    ISO-TP flow control messages (acknowledgements) to allow to
    receive ISO-TP messages actively instead of just snooping in on
    other people's conversations."""

    def __init__(self,
                 can_bus: can.BusABC,
                 can_rx_ids: list[int],
                 can_tx_ids: list[int],
                 padding_size: int = 0,
                 padding_value: int = 0xAA):
        self._can_bus = can_bus

        if isinstance(can_tx_ids, int):
            can_tx_ids = [can_tx_ids]

        self._can_tx_ids = can_tx_ids
        self._padding_size = padding_size
        self._padding_value = padding_value

        super().__init__(can_rx_ids)

        assert len(self._can_rx_ids) == len(self._can_tx_ids)
        assert set(self._can_rx_ids).isdisjoint(set(self._can_tx_ids))  # correct?

        self._block_size: list[int | None] = [None] * len(self._can_rx_ids)
        self._frames_received: list[int | None] = [None] * len(self._can_rx_ids)

    def can_tx_id(self, telegram_idx: int) -> int:
        """Given a Telegram index, returns the CAN ID for sending data.

        :raises TypeError: No transmission IDs specified (e.g.,
                           because we are passively decoding)
        :raises IndexError: The telegram index is invalid.
        """
        return self._can_tx_ids[telegram_idx]

    def on_single_frame(self, telegram_idx: int, frame_payload: bytes | bytearray) -> None:
        # send ACK
        # rx_id = self.can_rx_id(telegram_idx)
        tx_id = self.can_tx_id(telegram_idx)
        block_size = 0xFF
        min_separation_time = 0  # ms
        fc_payload = bitstruct.pack(
            "u4u4u8u8",
            IsoTp.FRAME_TYPE_FLOW_CONTROL,
            IsoTp.FLOW_CONTROL_CONTINUE,
            block_size,  # does not matter here?!
            min_separation_time,
        )

        self._send_can_message(tx_id, fc_payload)
        self._frames_received[telegram_idx] = None

        super().on_first_frame(telegram_idx, frame_payload)

    def on_first_frame(self, telegram_idx: int, frame_payload: bytes | bytearray) -> None:
        # send ACK
        # rx_id = self.can_rx_id(telegram_idx)
        tx_id = self.can_tx_id(telegram_idx)
        block_size = 0xFF  # default value, can be overwritten later
        min_separation_time = 0  # ms
        fc_payload = bitstruct.pack(
            "u4u4u8u8",
            IsoTp.FRAME_TYPE_FLOW_CONTROL,
            IsoTp.FLOW_CONTROL_CONTINUE,
            block_size,
            min_separation_time,
        )

        self._send_can_message(tx_id, fc_payload)

        self._block_size[telegram_idx] = block_size
        # TODO: find out if the first frame counts into the current block...
        self._frames_received[telegram_idx] = 0

        super().on_first_frame(telegram_idx, frame_payload)

    def on_consecutive_frame(self, telegram_idx: int, segment_idx: int,
                             frame_payload: bytes | bytearray) -> None:
        num_received = self._frames_received[telegram_idx]
        if num_received is None:
            # consequtive frame received before a first frame.
            # TODO (?): throw an exception
            return
        self._frames_received[telegram_idx] = num_received + 1

        # send new ACK if necessary
        block_size = self._block_size[telegram_idx]
        if block_size is not None and num_received >= block_size:
            # rx_id = self.can_rx_id(telegram_idx)
            tx_id = self.can_tx_id(telegram_idx)
            min_separation_time = 0  # ms
            fc_payload = bitstruct.pack(
                "u4u4u8u8",
                IsoTp.FRAME_TYPE_FLOW_CONTROL,
                IsoTp.FLOW_CONTROL_CONTINUE,
                block_size,
                min_separation_time,
            )
            self._send_can_message(tx_id, fc_payload)

            self._frames_received[telegram_idx] = 0  # TODO: 1?

        super().on_consecutive_frame(telegram_idx, segment_idx, frame_payload)

    def _send_can_message(self, can_tx_id: int, payload: bytes) -> None:
        if len(payload) < self._padding_size:
            payload = bytes(payload) + bytes([self._padding_value] *
                                             (self._padding_size - len(payload)))

        msg = can.Message(arbitration_id=can_tx_id, data=payload, is_extended_id=False)

        self._can_bus.send(msg)
