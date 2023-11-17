# SPDX-License-Identifier: MIT

import asyncio
from typing import Optional

import bitstruct
import can

from .isotp_state_machine import IsoTp, IsoTpStateMachine


class IsoTpConnection(IsoTpStateMachine):
    """
    This class extends the IsoTpStateMachine with the capability of
    sending out CAN-FD messages and reading ISOTP messages.
    """

    def __init__(self,
                 *,
                 can_bus: can.BusABC,
                 can_tx_id: int,
                 can_rx_id: int,
                 padding_value: int = 0xAA,
                 is_fd: bool = False):
        super().__init__(can_rx_ids=[can_rx_id])
        self._can_bus = can_bus
        self._can_tx_id = can_tx_id
        self._frame_size = 64 if is_fd else 8
        self._padding_value = bytes([padding_value])
        self._is_fd = is_fd

    async def read_telegram(self) -> bytes:
        async for x in self.read_telegrams(bus=self._can_bus):
            return x[1]
        raise Exception

    async def send_telegram(self, payload: bytes) -> None:
        """
        Sends out CAN telegrams (alias CAN messages) either CAN or CAN-FD.
        """
        if len(payload) <= 7:
            # add ISOTP frame type and flags
            payload = bitstruct.pack(f"u4u4r{len(payload)*8}", IsoTp.FRAME_TYPE_SINGLE,
                                     len(payload), payload)
            await self._send_can_message(self._can_tx_id, payload)
        else:
            chunks = []
            cursor = 0
            max_payload_size = 64 if self._is_fd else 8  # bytes
            while cursor < len(payload):
                if cursor == 0:
                    # FRAME_TYPE_FIRST has 2 bytes overhead
                    max_chunk_sz = max_payload_size - 2
                else:
                    # FRAME_TYPE_CONSECUTIVE has 1 byte overhead
                    max_chunk_sz = max_payload_size - 1

                chunks.append(payload[cursor:cursor + max_chunk_sz])
                cursor += max_chunk_sz

            for i, chunk in enumerate(chunks):
                if i == 0:
                    # -> first frame

                    # add ISOTP frame type and flags
                    frame_type = IsoTp.FRAME_TYPE_FIRST
                    frame_payload = bitstruct.pack(f"u4u12r{len(chunk)*8}", frame_type,
                                                   len(payload), chunk)
                else:
                    # -> consecutive frame

                    # add ISOTP frame type and flags
                    frame_type = IsoTp.FRAME_TYPE_CONSECUTIVE
                    frame_payload = bitstruct.pack(f"u4u4r{len(chunk)*8}", frame_type, i & 0xF,
                                                   chunk)

                await self._send_can_message(self._can_tx_id, frame_payload)

    async def _send_can_message(self,
                                can_tx_id: int,
                                payload: bytes,
                                padding_size: Optional[int] = None) -> None:
        if len(payload) < self._frame_size:
            payload = payload.ljust(self._frame_size, self._padding_value)

        msg = can.Message(
            arbitration_id=can_tx_id, data=payload, is_extended_id=True, is_fd=self._is_fd)

        write_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        loop.add_writer(self._can_bus, write_event.set)

        await write_event.wait()
        self._can_bus.send(msg, 0)
        write_event.clear()
