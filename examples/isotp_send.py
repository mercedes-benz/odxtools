#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import asyncio
import sys

import can

from odxtools.isotp_connection import IsoTpConnection

if len(sys.argv) != 6:
    print(f"Usage: {sys.argv[0]} CHANNEL RX_ID TX_ID PAYLOAD_STRING")
    print(f"")
    print(f"Send an ISO-TP telegram over a CAN bus using specified IDs")
    print(f"")
    print(f"Arguments:")
    print(f" CHANNEL         The device name of the CAN network interface (e.g., can0)")
    print(f" RX_ID           The CAN ID used by the peer for receiving (e.g., 0x600)")
    print(f" TX_ID           The CAN ID used by us for flow control (e.g., 0x601)")
    print(f" IS_FD           Specify if CAN-FD is to be used.")
    print(f' PAYLOAD_STRING  The string which ought to be send to the peer (e.g., "hello, world!")')
    sys.exit(1)

channel = sys.argv[1]
rx_id = int(sys.argv[2], 0)
tx_id = int(sys.argv[3], 0)
is_fd = sys.argv[4].lower() in ("true", "1")
payload = sys.argv[5].encode()


def isotp_error_handler(error: str) -> None:
    print(f"An isotp error occoured: {error}")


bus = can.Bus(bustype='socketcan', channel=sys.argv[1], receive_own_messages=True, fd=is_fd)

isotp_con = IsoTpConnection(can_bus=bus, can_tx_id=tx_id, can_rx_id=rx_id, is_fd=is_fd)


async def main() -> None:
    await isotp_con.send_telegram(payload)

    print("Payload transmission done.")

    bus.shutdown()


asyncio.run(main())
