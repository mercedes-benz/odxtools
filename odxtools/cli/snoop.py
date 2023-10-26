#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import argparse
import asyncio
import sys
from typing import Any, Type

import can

import odxtools.isotp_state_machine as ism
import odxtools.uds as uds
from odxtools.exceptions import DecodeError
from odxtools.isotp_state_machine import IsoTpStateMachine

from . import _parser_utils

# name of the tool
_odxtools_tool_name_ = "snoop"

odx_diag_layer = None
last_request = None

ecu_rx_id = None
ecu_tx_id = None


def handle_telegram(telegram_id: int, payload: bytes) -> None:
    global odx_diag_layer
    global last_request

    if telegram_id == ecu_tx_id:
        if uds.is_response_pending(payload):
            print(f" -> ECU: ... (response pending)")
            return

        decoded_message = None
        if last_request is not None:
            try:
                decoded_message = odx_diag_layer.decode_response(payload, last_request)
            except DecodeError:
                pass

        if decoded_message is not None:
            for i, resp in enumerate(decoded_message):
                params = resp.coding_object.parameters
                dec_str = ""
                if len(decoded_message) > 1:
                    dec_str = f" (decoding {i+1})"

                response_type = getattr(resp.coding_object, "response_type", None)
                rt_str = "unknown"
                if response_type == "POS-RESPONSE":
                    rt_str = "positive"
                elif response_type == "NEG-RESPONSE":
                    rt_str = "negative"

                print(f" -> {rt_str} ECU response{dec_str}: \"{resp.coding_object.short_name}\"")
                for param_name, param_val in resp.param_dict.items():
                    param = [x for x in params if x.short_name == param_name][0]
                    if not param.is_settable:
                        continue
                    print(f"      {param_name} = {repr(param_val)}")
        else:
            print(f" -> ECU response: unrecognized response of {len(payload)} bytes length: "
                  f"0x{payload.hex()}")

        return

    decoded_message = None
    if odx_diag_layer is not None:
        try:
            decoded_message = odx_diag_layer.decode(payload)[0]
            last_request = payload
        except DecodeError:
            last_request = None

    if decoded_message is not None:
        print(f"tester request: \"{decoded_message.coding_object.short_name}\"")
        params = decoded_message.coding_object.parameters
        for param_name, param_val in decoded_message.param_dict.items():
            param = [x for x in params if x.short_name == param_name][0]
            if not param.is_settable:
                continue
            print(f"  {param_name} = {repr(param_val)}")

    else:
        print(f"Tester: "
              f"{payload.hex()} "
              f"({payload!r}, {len(payload)} bytes)")


def init_verbose_state_machine(BaseClass: Type[IsoTpStateMachine], *args: Any,
                               **kwargs: Any) -> IsoTpStateMachine:

    class InformativeIsoTpDecoder(BaseClass):  # type: ignore[valid-type, misc]

        def on_sequence_error(self, telegram_idx: int, expected_idx: int, rx_idx: int) -> None:
            rx_can_id = self.can_rx_id(telegram_idx)
            print(f"Sequence error for ID 0x{rx_can_id:x}: "
                  f"Received sequence number {rx_idx} but expected {expected_idx}")

            super().on_sequence_error(telegram_idx, expected_idx, rx_idx)

        def on_frame_type_error(self, telegram_idx: int, frame_type: int) -> None:
            rx_can_id = self.can_rx_id(telegram_idx)

            print(f"Invalid ISO-TP frame for CAN ID 0x{rx_can_id:x}: {frame_type}")

    return InformativeIsoTpDecoder(*args, **kwargs)


async def active_main(args: argparse.Namespace) -> None:
    global ecu_rx_id, ecu_tx_id

    can_bus = can.Bus(channel=args.channel, bustype="socketcan")

    ecu_rx_id = int(args.rx, 0)
    ecu_tx_id = int(args.tx, 0)
    isotp_decoder = init_verbose_state_machine(
        BaseClass=ism.IsoTpActiveDecoder,
        can_bus=can_bus,
        can_rx_ids=ecu_rx_id,
        can_tx_ids=ecu_tx_id,
        padding_size=8,
    )

    print(f"Reacting to messages on channel {args.channel}")
    async for telegram_id, payload in isotp_decoder.read_telegrams(can_bus):
        handle_telegram(telegram_id, payload)


async def passive_main(args: argparse.Namespace) -> None:
    global ecu_rx_id, ecu_tx_id

    ecu_rx_id = int(args.rx, 0)
    ecu_tx_id = int(args.tx, 0)

    isotp_decoder = init_verbose_state_machine(
        BaseClass=ism.IsoTpStateMachine, can_rx_ids=[ecu_rx_id, ecu_tx_id])

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


def add_cli_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--active",
        "-a",
        metavar="active_mode",
        default=False,
        action="store_const",
        const=True,
        required=False,
        help="Active mode, sends flow control messages to receive ISO-TP telegrams successfully",
    )
    parser.add_argument(
        "--channel",
        "-c",
        default=None,
        help="CAN interface name to be used (required in active mode)",
    )
    parser.add_argument(
        "--rx",
        "-r",
        default=None,
        required=False,
        help="CAN ID in which the ECU listens for diagnostic messages",
    )
    parser.add_argument(
        "--tx",
        "-t",
        default=None,
        required=False,
        help="CAN ID in which the ECU sends replys to diagnostic messages  (required in active mode)",
    )
    parser.add_argument(
        "--variant",
        "-v",
        default=None,
        required=False,
        help="Name of the ECU variant which the decode process ought to be based on",
    )
    parser.add_argument(
        "--protocol",
        "-p",
        default=None,
        required=False,
        help="Name of the protocol used for decoding",
    )
    _parser_utils.add_pdx_argument(parser)


def add_subparser(subparsers: "argparse._SubParsersAction") -> None:
    parser = subparsers.add_parser(
        "snoop",
        description="Live decoding of a diagnostic session.",
        help="Live decoding of a diagnostic session.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_cli_arguments(parser)


def run(args: argparse.Namespace) -> None:
    global odx_diag_layer
    odx_database = _parser_utils.load_file(args)

    if (odx_database is not None or args.variant is not None) and (odx_database is None or
                                                                   args.variant is None):
        print("The database and variant must always either be "
              "both specified or not at all")
        sys.exit(1)

    odx_diag_layer = None
    if odx_database is not None:
        odx_diag_layer = odx_database.diag_layers.get(args.variant)

        if odx_diag_layer is None:
            print(f"Variant '{args.variant}' does not exist. Available variants:")
            for dl in odx_database.diag_layers:
                desc = "" if dl.description is None else f": {dl.description}"
                print(f"  {dl.short_name}{desc}")
            sys.exit(1)

    protocol_name = args.protocol
    if odx_diag_layer is not None and protocol_name is not None:
        protocol_names = [x.short_name for x in odx_diag_layer.protocols]
        if protocol_name not in protocol_names:
            print(f"ECU variant {odx_diag_layer.short_name} does not support "
                  f"a protocol named '{protocol_name}'. Supported protocols are:")
            for x in odx_diag_layer.protocols:
                desc = "" if x.description is None else f": {x.description}"
                print(f"  {x.short_name}{desc}")
            sys.exit(1)

    # if no can IDs have been explicitly specified, take them from the DL
    if args.rx is None and odx_diag_layer:
        args.rx = str(odx_diag_layer.get_can_receive_id(protocol_name=protocol_name))

    if args.tx is None and odx_diag_layer:
        args.tx = str(odx_diag_layer.get_can_send_id(protocol_name=protocol_name))

    if args.rx is None:
        print(f"Could not determine a CAN receive ID.")
        sys.exit(1)

    if args.active:
        asyncio.run(active_main(args))
    else:
        asyncio.run(passive_main(args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode ISO-TP communication over a can bus")

    add_cli_arguments(parser)

    args = parser.parse_args()  # deals with the help message handling

    run(args)
