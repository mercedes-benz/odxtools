# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from enum import IntEnum
from itertools import chain
from typing import Optional, Union, ByteString

import odxtools.obd as obd

class UDSSID(IntEnum):
    """The service IDs standardized by UDS.

    For additional information, see https://en.wikipedia.org/wiki/Unified_Diagnostic_Services
    """
    # 0x10..0x3e: UDS standardized service IDs
    DiagnosticSessionControl = 0x10
    EcuReset = 0x11
    SecurityAccess = 0x27
    CommunicationControl = 0x28
    Authentication = 0x29
    TesterPresent = 0x3E
    AccessTimingParameters = 0x83
    SecuredDataTransmission = 0x84
    ControlDtcSettings = 0x85
    ResponseOnEvent = 0x86
    LinkControl = 0x87
    ReadDataByIdentifier = 0x22
    ReadMemoryByAddress = 0x23
    ReadScalingDataByIdentifier = 0x24
    ReadDataByIdentifierPeriodic = 0x2A
    DynamicallyDefineDataIdentifier = 0x2C
    WriteDataByIdentifier = 0x2E
    WriteMemoryByAddress = 0x3D
    ClearDiagnosticInformation = 0x14
    ReadDtcInformation = 0x19
    InputOutputControlByIdentifier = 0x2F
    RoutineControl = 0x31
    RequestDownload = 0x34
    RequestUpload = 0x35
    TransferData = 0x36
    RequestTransferExit = 0x37
    RequestFileTransfer = 0x38

    # 0x81..0x82: KWP on K-Line

    # 0xA0..0xB9: Reserved for OEM specific services

    # 0xBA..0xBE: Reserved for ECU specific services

# add the OBD SIDs to the ones from UDS
SID = IntEnum('UdsSID', ((i.name, i.value) for i in chain(obd.SID, UDSSID)))  # type: ignore

class NegativeResponseCodes(IntEnum):
    """The standardized negative response codes of UDS.

    In UDS, negative responses always exhibit the format `[0x7f,
    service_id_of_request, response_code]`. The meaning of the last
    byte is what's defined here.
    """
    GeneralReject = 0x10
    ServiceNotSupported = 0x11
    SubFunctionNotSupported = 0x12
    InvalidFormat = 0x13 # Incorrect message length of request or invalid format
    TooLong = 0x14 # Response would be too long
    Busy = 0x21 # please repeat!
    ConditionsIncorrect = 0x22 # request cannot be satisfied because ECU is in wrong state
    RequestSequenceError = 0x24
    NoResponseFromSubNetComponent = 0x25 # we pinged a slave ECU bit it did not respond in time
    Failure = 0x26 # failure prevents execution of requested action
    RequestOutOfRange = 0x31
    SecurityAccessDenied = 0x33
    InvalidKey = 0x35
    ExceededNumberOfAttempts = 0x36
    RequiredTimeDelayNotExpired = 0x37
    Reserved = 0x4F # reserved by Extended Data Link Security Document
    UpDownloadNotAccepted = 0x70
    TransferDataSuspended = 0x71
    GeneralProgrammingFailure = 0x72
    WrongBlockSequenceCounter = 0x73
    ResponsePending = 0x78 # Request correctly received, but response is still pending
    SubFunctionNotSupportedInActiveSession = 0x7E
    ServiceNotSupportedInActiveSession = 0x7F

# get the ID of a positive response
def positive_response_id(service_id: int) -> int:
    """Given a service ID of a request, return the corresponding SID for a positive response"""
    assert service_id != 0x7f - 0x40
    return service_id + 0x40

NegativeResponseId = 0x7f
def negative_response_id(service_id: int) -> int:
    """Given a service ID of a request, return the corresponding SID for a negative response"""
    assert service_id != 0x7f - 0x40  # TODO: What is this assert supposed to do?
    return NegativeResponseId

def is_reponse_pending(telegram_payload: ByteString, request_sid: Optional[int] = None) -> bool:
    # "response pending" responses exhibit at least three bytes
    if len(telegram_payload) < 3:
        return False

    sid = telegram_payload[0]
    rq_sid = telegram_payload[1]
    resp_code = telegram_payload[2]

    # "response pending" answers are always negative
    if sid != NegativeResponseId:
        return False

    # if a request SID was specified for this function, it must be
    # identical to the one which we received on the wire. (if none was
    # specified, we don't care about the received SID)
    if request_sid is not None and request_sid != rq_sid:
        return False

    # if the response code is not ResponsePending (0x78), the received
    # telegram is another error
    if resp_code != NegativeResponseCodes.ResponsePending:
        return False

    # if all of the above applies, we received a "stay tuned" response
    return True
