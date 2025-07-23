#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
#
# Implementation of the "lazy" somersault ECU
import argparse
import asyncio
import logging
import random
from socket import socket
from typing import cast

import isotp
import isotp.tpsock
import somersaultecu

import odxtools.uds as uds
from odxtools.exceptions import DecodeError, odxrequire
from odxtools.message import Message
from odxtools.odxtypes import ParameterValueDict
from odxtools.response import Response, ResponseType

from .somersaultecu import database as somersaultdatabase

tester_logger = logging.getLogger("somersault_lazy_tester")
ecu_logger = logging.getLogger("somersault_lazy_ecu")

is_sterile = False
can_channel: str | None = None
somersault_lazy_diag_layer = somersaultdatabase.ecus.somersault_lazy

# the raw payload data of the telegrams received by the ECU and by the
# tester when in sterile mode (unittest without a CAN channel)
sterile_rx_ecu: list[bytes] = []
sterile_rx_ecu_event: asyncio.Event | None = None
sterile_rx_tester: list[bytes] = []
sterile_rx_tester_event: asyncio.Event | None = None


def create_isotp_socket(channel: str | None, rxid: int, txid: int) -> isotp.tpsock.socket | None:
    if is_sterile:
        return None

    assert channel is not None

    # create an ISO-TP socket without a timeout (timeouts are handled
    # using asyncio). Also, for asyncio to work with this socket, it
    # must be non-blocking...
    result_socket = isotp.socket(timeout=None)
    result_socket._socket.setblocking(False)

    # set the ISO-TP flow control options:
    #
    # stmin: minimum frame separation time [ms]
    # bs: maximum block size. (Must be smaller than 4096?)
    result_socket.set_fc_opts(stmin=5, bs=100)

    # instruct the ISO-TP subsystem to pad the last CAN frame of a
    # telegram to 8 bytes of payload using 0xcc padding bytes
    result_socket.set_opts(txpad=0xCC)

    isotp_addr = isotp.Address(rxid=rxid, txid=txid)
    result_socket.bind(channel, address=isotp_addr)

    return result_socket


async def ecu_send(isotp_socket: isotp.tpsock.socket | None, payload: bytes | bytearray) -> None:
    """
    ECU sends a message, either in "sterile" or in "live" mode.
    """
    global sterile_rx_tester
    global sterile_rx_tester_event

    if is_sterile:
        assert isotp_socket is None
        assert sterile_rx_tester_event is not None

        sterile_rx_tester_event.clear()
        sterile_rx_tester.append(bytes(payload))
        sterile_rx_tester_event.set()
    else:
        assert isotp_socket is not None

        loop = asyncio.get_running_loop()
        await loop.sock_sendall(cast(socket, isotp_socket), payload)


async def ecu_recv(isotp_socket: isotp.tpsock.socket | None) -> bytes:
    """
    ECU receives a message, either in "sterile" or in "live" mode.
    """
    global sterile_rx_ecu
    global sterile_rx_ecu_event

    if is_sterile:
        assert isotp_socket is None
        assert sterile_rx_ecu_event is not None

        if len(sterile_rx_ecu) > 0:
            return sterile_rx_ecu.pop(0)

        sterile_rx_ecu_event.clear()
        await sterile_rx_ecu_event.wait()
        sterile_rx_ecu_event.clear()

        return sterile_rx_ecu.pop(0)
    else:
        assert isotp_socket is not None

        loop = asyncio.get_running_loop()
        return await loop.sock_recv(cast(socket, isotp_socket), 4095)


async def tester_send(isotp_socket: isotp.tpsock.socket | None, payload: bytes | bytearray) -> None:
    """
    Tester sends a message, either in "sterile" or in "live" mode.
    """
    global sterile_rx_ecu
    global sterile_rx_ecu_event

    if is_sterile:
        assert isotp_socket is None
        assert sterile_rx_ecu_event is not None

        sterile_rx_ecu.append(bytes(payload))
        sterile_rx_ecu_event.set()
    else:
        assert isotp_socket is not None

        loop = asyncio.get_running_loop()
        await loop.sock_sendall(cast(socket, isotp_socket), payload)


async def tester_recv(isotp_socket: isotp.tpsock.socket | None) -> bytes:
    """
    Tester receives a message, either in "sterile" or in "live" mode.
    """
    global sterile_rx_tester
    global sterile_rx_tester_event

    if is_sterile:
        assert isotp_socket is None
        assert sterile_rx_tester_event is not None

        if len(sterile_rx_tester) > 0:
            return sterile_rx_tester.pop(0)

        sterile_rx_tester_event.clear()
        await sterile_rx_tester_event.wait()
        sterile_rx_tester_event.clear()

        return sterile_rx_tester.pop(0)
    else:
        assert isotp_socket is not None

        loop = asyncio.get_running_loop()
        return await loop.sock_recv(cast(socket, isotp_socket), 4095)


class SomersaultLazyEcu:

    def __init__(self) -> None:
        self._diag_session_open = False
        self._data_receive_event = asyncio.Event()
        self.dizziness_level = 0
        self.max_dizziness_level = 10

        self.isotp_socket = create_isotp_socket(
            can_channel,
            rxid=odxrequire(somersault_lazy_diag_layer.get_can_receive_id()),
            txid=odxrequire(somersault_lazy_diag_layer.get_can_send_id()),
        )

        ##############
        # extract the tester present parameters from the ECU's
        # communication parameters.
        ##############

        # determine the timeout on inactivity [s]
        self._idle_timeout = somersault_lazy_diag_layer.get_tester_present_time() or 3.0

        # we send a response to tester present messages. make sure
        # that this is specified
        cp = odxrequire(somersault_lazy_diag_layer.get_comparam("CP_TesterPresentReqRsp"))
        assert cp.value == "Response expected" or cp.value == "1"

    async def _handle_requests_task(self) -> None:
        while True:
            data = await ecu_recv(self.isotp_socket)

            # to whom it may concern: we have received some data. This
            # is used to make sure that we do not run into the "no
            # tester present" timeout and close the session spuriously
            self._data_receive_event.set()

            ecu_logger.debug(f"Data received: 0x{data.hex()}")

            # decode the data
            try:
                messages = somersault_lazy_diag_layer.decode(data)

                # do the actual work which we were asked to do. we assume
                # that requests can always be uniquely decoded
                assert len(messages) == 1
                await self._handle_request(messages[0])
            except DecodeError as e:
                ecu_logger.warning(f"Could not decode request "
                                   f"0x{data.hex()}: {e}")
                return

    async def _handle_request(self, message: Message) -> None:
        service = message.service

        ecu_logger.info(f"received UDS message: {service.short_name}")

        # keep alive message.
        if service.short_name == "tester_present":
            # send a positive response if have an active diagnostic
            # session, and a negative one if we don't.
            if self._diag_session_open:
                response_payload = service.positive_responses[0].encode(
                    coded_request=message.coded_message)
            else:
                response_payload = service.negative_responses[0].encode(
                    coded_request=message.coded_message)

            await ecu_send(self.isotp_socket, response_payload)
            return

        if service.short_name == "session_start":
            if not self._diag_session_open:
                response_payload = service.positive_responses[0].encode(
                    coded_request=message.coded_message, can_do_backward_flips="false")
            else:
                response_payload = service.negative_responses[0].encode(
                    coded_request=message.coded_message)

            self._diag_session_open = True
            await ecu_send(self.isotp_socket, response_payload)
            return

        # from here on, a diagnostic session must be started or else
        # we will send a generic "ServiceNotSupportedInActiveSession"
        # UDS response
        if not self._diag_session_open:
            rq_id = 0
            if message.coded_message:
                rq_id = message.coded_message[0]

            # send a "service not supported in active session" UDS
            # response.
            await ecu_send(self.isotp_socket, bytes([0x7F, rq_id, 0x7F]))
            return

        # stop the diagnostic session
        if service.short_name == "session_stop":
            if self._diag_session_open:
                response_payload = service.positive_responses[0].encode(
                    coded_request=message.coded_message)
            else:
                response_payload = service.negative_responses[0].encode(
                    coded_request=message.coded_message)

            self._diag_session_open = False
            await ecu_send(self.isotp_socket, response_payload)
            return

        if service.short_name == "do_forward_flips":
            await self._handle_forward_flip_request(message)
            return

    async def _handle_forward_flip_request(self, message: Message) -> None:
        service = message.service
        # TODO: the need for .param_dict is quite ugly IMO,
        # i.e. provide a __getitem__() method for the Message class() (?)
        soberness_check = message.param_dict["forward_soberness_check"]
        num_flips = message.param_dict["num_flips"]

        if soberness_check != 0x12:
            response = service.negative_responses.flips_not_done
            response_data = response.encode(
                coded_request=message.coded_message,
                reason=0,  # -> not sober
                flips_successfully_done=0,
            )
            await ecu_send(self.isotp_socket, response_data)
            return

        # we cannot do all flips because we are too dizzy
        assert isinstance(num_flips, int)
        if self.dizziness_level + num_flips > self.max_dizziness_level:

            response = service.positive_responses.grudging_forward
            response_data = response.encode(
                coded_request=message.coded_message,
                reason=1,  # -> too dizzy
                flips_successfully_done=self.max_dizziness_level - self.dizziness_level,
            )
            await ecu_send(self.isotp_socket, response_data)
            self.dizziness_level = self.max_dizziness_level
            return

        # do the flips, but be aware that 1% of our attempts fail
        # because we stumble
        for i in range(0, num_flips):
            if random.randrange(0, 10000) < 100:
                response = service.negative_responses.flips_not_done
                response_data = response.encode(
                    coded_request=message.coded_message,
                    reason=2,  # -> stumbled
                    flips_successfully_done=i,
                )
                await ecu_send(self.isotp_socket, response_data)
                return

            self.dizziness_level += 1

        response = service.positive_responses.grudging_forward
        response_data = response.encode(coded_request=message.coded_message)
        await ecu_send(self.isotp_socket, response_data)

    def close_diag_session(self) -> None:
        if not self._diag_session_open:
            return

        self._diag_session_open = False

        # clean up data associated with the diagnostic session

    async def run(self) -> None:
        ecu_logger.info("running diagnostic server")

        cst = self._auto_close_session_task()
        hrt = self._handle_requests_task()

        await asyncio.gather(cst, hrt)

    async def _auto_close_session_task(self) -> None:
        # task to close the diagnostic session if the tester has not
        # been seen for longer than the timeout specified by the ECU.
        while True:
            # sleep until we either hit our timeout or we've received
            # some data from the tester
            try:
                await asyncio.wait_for(self._data_receive_event.wait(), self._idle_timeout * 1.05)
            except asyncio.exceptions.TimeoutError:
                # we ran into the idle timeout. Close the diagnostic
                # session if it is open. note that this also happens if
                # there is no active diagnostic session
                self.close_diag_session()
                continue
            except asyncio.exceptions.CancelledError:
                return

            if self._data_receive_event.is_set():
                # we have received some data
                self._data_receive_event.clear()
                continue


async def tester_await_response(isotp_socket: isotp.tpsock.socket | None,
                                raw_message: bytes | bytearray,
                                timeout: float = 0.5) -> bytes | ParameterValueDict:
    # await the answer from the server (be aware that the maximum
    # length of ISO-TP telegrams over the CAN bus is 4095 bytes)
    raw_response = await tester_recv(isotp_socket)

    tester_logger.debug(f"received response")

    try:
        replies = somersault_lazy_diag_layer.decode_response(raw_response, raw_message)
        assert len(replies) == 1  # replies must always be uniquely decodable
        assert isinstance(replies[0].coding_object, Response)

        if replies[0].coding_object.response_type == ResponseType.POSITIVE:
            rtype = "positive"
        elif replies[0].coding_object.response_type == ResponseType.NEGATIVE:
            rtype = "negative"
        else:
            rtype = "unknown"

        tester_logger.debug(f"received {rtype} response")

        return replies[0].param_dict

    except DecodeError as e:
        if len(raw_response) >= 3:
            sid = raw_response[0]
            rq_sid = raw_response[1]
            error_id = raw_response[2]

            if sid == uds.NegativeResponseId:
                try:
                    rq_name = somersaultecu.SID(rq_sid).name
                except ValueError:
                    rq_name = f"0x{rq_sid:x}"
                error_name = uds.NegativeResponseCodes(error_id).name

                tester_logger.debug(
                    f"Received negative response by service {rq_name}: {error_name}")
                return raw_response

        tester_logger.debug(f"Could not decode response: {e}")
        return raw_response


async def tester_main() -> None:
    tester_logger.info("running diagnostic tester")

    # note that ODX specifies the CAN IDs from the ECU's point of
    # view, i.e., from the tester's (our) perspective, they are
    # reversed.
    isotp_socket = create_isotp_socket(
        can_channel,
        txid=odxrequire(somersault_lazy_diag_layer.get_can_receive_id()),
        rxid=odxrequire(somersault_lazy_diag_layer.get_can_send_id()),
    )

    # try to to do a single forward flip without having an active session (ought to fail)
    tester_logger.debug(f"attempting a sessionless forward flip")
    raw_message = somersault_lazy_diag_layer.services.do_forward_flips(
        forward_soberness_check=0x12, num_flips=1)
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    # send "start session"
    tester_logger.debug(f"starting diagnostic session")
    raw_message = somersault_lazy_diag_layer.services.session_start()
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    # attempt to do a single forward flip
    tester_logger.debug(f"attempting a forward flip")
    raw_message = somersault_lazy_diag_layer.services.do_forward_flips(
        forward_soberness_check=0x12, num_flips=1)
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    # attempt to do a single forward flip but fail the soberness check
    tester_logger.debug(f"attempting a forward flip")
    raw_message = somersault_lazy_diag_layer.services.do_forward_flips(
        forward_soberness_check=0x23, num_flips=1)
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    # attempt to do three forward flips
    tester_logger.debug(f"attempting three forward flip")
    raw_message = somersault_lazy_diag_layer.services.do_forward_flips(
        forward_soberness_check=0x12, num_flips=3)
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    # attempt to do 50 forward flips (should always fail because of dizzyness)
    tester_logger.debug(f"attempting 50 forward flip")
    raw_message = somersault_lazy_diag_layer.services.do_forward_flips(
        forward_soberness_check=0x12, num_flips=50)
    await tester_send(isotp_socket, raw_message)
    await tester_await_response(isotp_socket, raw_message)

    tester_logger.debug(f"Finished")


async def main(args: argparse.Namespace) -> None:
    global is_sterile
    global sterile_rx_ecu_event
    global sterile_rx_tester_event

    if args.mode == "unittest":
        is_sterile = args.channel is None
        sterile_rx_ecu_event = asyncio.Event()
        sterile_rx_tester_event = asyncio.Event()
    elif args.channel is None:
        print("A CAN channel must be specified when not in unittest mode.")
        return

    # TODO: handle ISO-TP communication parameters (block size,
    # timings, ...) specified by the Somersault ECU
    tester_task = None
    if args.mode != "server":
        tester_task = asyncio.create_task(tester_main())

    server_task = None
    if args.mode != "tester":
        somersault_ecu = SomersaultLazyEcu()
        server_task = asyncio.create_task(somersault_ecu.run())

    if args.mode == "server":
        assert server_task is not None
        await server_task
    elif args.mode == "tester":
        assert tester_task is not None
        await tester_task
    else:
        assert args.mode == "unittest"
        assert server_task is not None
        assert tester_task is not None

        # run both tasks in parallel. Since the server task does not
        # complete, we need to wait until the first task is completed
        # and then manually that this was the server task
        done, pending = await asyncio.wait([tester_task, server_task],
                                           return_when=asyncio.FIRST_COMPLETED)

        if tester_task in pending:
            tester_logger.error("The tester task did not terminate. This "
                                "should *never* happen!")
            tester_task.cancel()

        if server_task not in pending:
            ecu_logger.error("The server task terminated. This "
                             "should *never* happen!")
        else:
            # since if everything goes according to plan only the
            # tester terminates, we need to stop server task here to
            # avoid complaints from asyncio...
            server_task.cancel()


parser = argparse.ArgumentParser(
    description="Provides an implementation for the 'lazy' variant of the somersault ECU")

parser.add_argument(
    "--channel",
    "-c",
    required=False,
    help="CAN interface name to be used (required for tester or server modes)",
)
parser.add_argument(
    "--mode",
    "-m",
    default="unittest",
    required=False,
    help="Specify whether to start the ECU side ('server'), the tester side ('tester') or both ('unittest')",
)

args = parser.parse_args()  # deals with the help message handling

# set the verbosity of the log output
logging.basicConfig(level=logging.DEBUG)  # log messages from the ECU itself
logging.getLogger("odxtools").setLevel(
    logging.WARNING)  # log messages stemming from the odxtools library

can_channel = args.channel

asyncio.run(main(args))
