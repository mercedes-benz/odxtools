#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import isotp
import sys
import can
import time

if len(sys.argv) != 5:
    print(f"Usage: {sys.argv[0]} CHANNEL RX_ID TX_ID PAYLOAD_STRING")
    print(f"")
    print(f"Send an ISO-TP telegram over a CAN bus using specified IDs")
    print(f"")
    print(f"Arguments:")
    print(f" CHANNEL         The device name of the CAN network interface (e.g., can0)")
    print(f" RX_ID           The CAN ID used by the peer for receiving (e.g., 0x600)")
    print(f" TX_ID           The CAN ID used by us for flow control (e.g., 0x601)")
    print(f" PAYLOAD_STRING  The string which ought to be send to the peer (e.g., \"hello, world!\")")
    sys.exit(1)

channel = sys.argv[1]
rx_id = int(sys.argv[2], 0)
tx_id = int(sys.argv[3], 0)
payload = sys.argv[4].encode()

def isotp_error_handler(error):
    print(f"An isotp error occoured: {error}")

isotp_socket = isotp.socket()

# set the ISO-TP flow control options:
#
# stmin: minimum frame separation time [ms]
# bs: maximum block size. (Must be smaller than 4096?)
isotp_socket.set_fc_opts(stmin=5, bs=100)

can_bus = can.Bus(channel=channel, bustype="socketcan")

# note that we specify the CAN IDs from the ECU's point of view, i.e.,
# from the tester's (our) perspective, they are reversed.
isotp_addr = isotp.Address(rxid=tx_id, txid=rx_id)

isotp_stack = isotp.CanStack(can_bus,
                             address=isotp_addr,
                             error_handler=isotp_error_handler)

isotp_stack.send(payload)

while isotp_stack.transmitting():
   isotp_stack.process()
   time.sleep(isotp_stack.sleep_time())

print("Payload transmission done.")

can_bus.shutdown()
