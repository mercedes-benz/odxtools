#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import sys
import argparse
import can
import asyncio

from . import _parser_utils
import odxtools
import odxtools.uds as uds
import odxtools.isotp_state_machine as ism

# name of the tool
_odxtools_tool_name_ = "snoop"

odx_diag_layer = None
last_request = None

ecu_rx_id = None
ecu_tx_id = None


def handle_telegram(telegram_id, payload):
    global odx_diag_layer
    global last_request

    if telegram_id == ecu_tx_id:
        if uds.is_reponse_pending(payload):
            print(f" -> response pending")
            return

        decoded_message = None
        if last_request is not None:
            try:
                decoded_message = odx_diag_layer.decode_response(
                    payload, last_request)[0]
            except odxtools.DecodeError:
                pass

        if decoded_message is not None:
            print(f" -> {decoded_message}")
        else:
            print(f" -> unrecognized response of {len(payload)} bytes length: "
                  f"0x{payload.hex()}")

        return

    decoded_message = None
    if odx_diag_layer is not None:
        try:
            decoded_message = odx_diag_layer.decode(payload)[0]
            last_request = payload
        except odxtools.DecodeError:
            last_request = None

    if decoded_message:
        print(f"Tester: {decoded_message}")
    else:
        print(f"Tester: "
              f"{payload.hex()} "
              f"({payload}, {len(payload)} bytes)")


def init_verbose_state_machine(BaseClass, *args, **kwargs):
    class InformativeIsoTpDecoder(BaseClass):
        def on_sequence_error(self, telegram_idx, expected_idx, rx_idx):
            rx_can_id = self.can_rx_id(telegram_idx)
            print(f"Sequence error for ID 0x{rx_can_id:x}: "
                  f"Received sequence number {rx_idx} but expected {expected_idx}")

            super(BaseClass, self).on_sequence_error(
                telegram_idx, expected_idx, rx_idx)

        def on_frame_type_error(self, telegram_idx, frame_type):
            rx_can_id = self.can_rx_id(telegram_idx)

            print(
                f"Invalid ISO-TP frame for CAN ID 0x{rx_can_id:x}: {frame_type}")

    return InformativeIsoTpDecoder(*args, **kwargs)


async def active_main(args):
    global ecu_rx_id, ecu_tx_id

    can_bus = can.Bus(channel=args.channel, bustype="socketcan")

    ecu_rx_id = int(args.rx, 0)
    ecu_tx_id = int(args.tx, 0)
    isotp_decoder = init_verbose_state_machine(BaseClass=ism.IsoTpActiveDecoder,
                                               can_bus=can_bus,
                                               can_rx_ids=ecu_rx_id,
                                               can_tx_ids=ecu_tx_id,
                                               padding_size=8)

    print(f"Reacting to messages on channel {args.channel}")
    async for telegram_id, payload in isotp_decoder.read_telegrams(can_bus):
        handle_telegram(telegram_id, payload)


async def passive_main(args):
    global ecu_rx_id, ecu_tx_id

    ecu_rx_id = int(args.rx, 0)
    ecu_tx_id = int(args.tx, 0)
    isotp_decoder = init_verbose_state_machine(BaseClass=ism.IsoTpStateMachine,
                                               can_rx_ids=[ecu_rx_id, ecu_tx_id])

    if args.channel:
        # decode a "real" bus
        can_bus = can.Bus(channel=args.channel, bustype="socketcan")

        print(f"Decoding messages on channel {args.channel}")
        async for telegram_id, payload in isotp_decoder.read_telegrams(can_bus):
            handle_telegram(telegram_id, payload)
    else:
        # decode data from stdin
        async for telegram_id, payload in isotp_decoder.read_telegrams(sys.stdin):
            handle_telegram(telegram_id, payload)


def add_cli_arguments(parser):
    parser.add_argument("--active", "-a", metavar="active_mode", default=False, action='store_const', const=True, required=False,
                        help="Active mode, sends flow control messages to receive ISO-TP telegrams successfully")
    parser.add_argument("--channel", "-c", default=None,
                        help="CAN interface name to be used (required in active mode)")
    parser.add_argument("--rx", "-r", default=None, required=False,
                        help="CAN ID in which the ECU listens for diagnostic messages")
    parser.add_argument("--tx", "-t", default=None, required=False,
                        help="CAN ID in which the ECU sends replys to diagnostic messages  (required in active mode)")
    parser.add_argument("--variant", "-v", default=None, required=False,
                        help="Name of the ECU variant which the decode process ought to be based on")
    _parser_utils.add_pdx_argument(parser)


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        'snoop',
        description="Live decoding of a diagnostic session.",
        help="Live decoding of a diagnostic session.",
        formatter_class=argparse.RawTextHelpFormatter)
    add_cli_arguments(parser)


def run(args, odx_database=None):
    global odx_diag_layer
    odx_database = _parser_utils.load_file(args)

    if (odx_database is not None or args.variant is not None) and \
       (odx_database is None or args.variant is None):
        print("The database and variant must always either be "
              "both specified or not at all")
        sys.exit(1)

    odx_diag_layer = None
    if odx_database is not None:
        odx_diag_layer = odx_database.diag_layers[args.variant]

        if odx_diag_layer is None:
            print(
                f"Variant '{args.variant}' does not exist. Available variants:")
            for dl in odx_database.diag_layers:
                print(f"  {dl.short_name}")
            sys.exit(1)

    # if no can IDs have been explicitly specified, take them from the DL
    if args.rx is None and odx_diag_layer:
        args.rx = str(odx_diag_layer.get_receive_id())

    if args.tx is None and odx_diag_layer:
        args.tx = str(odx_diag_layer.get_send_id())

    if args.rx is None:
        print(
            f"If no database and variant is specified, a CAN receive ID must be provided.")
        sys.exit(1)

    if args.active:
        asyncio.run(active_main(args))
    else:
        asyncio.run(passive_main(args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Decode ISO-TP communication over a can bus")

    add_cli_arguments(parser)

    args = parser.parse_args()  # deals with the help message handling

    odx_database = odxtools.load_pdx_file(args.pdx_file)

    run(args, odx_database)
