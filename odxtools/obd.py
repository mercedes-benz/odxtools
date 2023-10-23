# SPDX-License-Identifier: MIT
from enum import IntEnum
from typing import Optional


class SID(IntEnum):
    """The standardized service IDs for ODB-II (SAE J1979).

    The physical CAN address to which OBD-II (functional) requests are
    to be send to is usually 0x7DF and CAN frames must be padded to 8
    bytes (with 0xcc as the padding pattern, i.e., one byte by ISO-TP
    and "actual" 7 payload bytes). Some vehicles support addressing up
    to seven additional ECUs via OBD-II which use the CAN IDs 0x7DF +
    $I.

    The physical CAN ID for responses of such requests is the CAN
    request ID plus 8 (i.e. usually 0x7E8).

    For additional information, see https://en.wikipedia.org/wiki/OBD-II_PIDs

    """

    # 0x00..0x0a: service IDs for emissions systems from ISO15031-5
    ShowCurrentData = 0x01
    ShowFreezeFrameData = 0x02
    ShowStoredDiagnosticTroubleCodes = 0x03
    ClearDiagnosticTroubleCodesAndStoredValues = 0x04
    OxygenSensorMonitoringTestResults = 0x05
    OtherTestResults = 0x06
    ShowPendingDiagnosticTroubleCodes = 0x07
    ControlOperationOfOnboardComponentOrSystem = 0x08
    RequestVehicleInformation = 0x09
    PermanentDiagnosticTroubleCodes = 0x0A


_sid_to_name = {
    0x01: "Show Current Data",
    0x02: "Show Freeze Frame Data",
    0x03: "Show Stored Diagnostic Trouble Codes",
    0x04: "Clear Diagnostic Trouble Codes and Stored Values",
    0x05: "Test Results, non-CAN Oxygen Sensor Monitoring",
    0x06: "Test Results, CAN Oxygen Sensor Monitoring",
    0x07: "Show Pending Diagnostic Trouble Codes",
    0x08: "Control Operation of Onboard Component or System",
    0x09: "Request Vehicle Information",
    0x0A: "Permanent Diagnostic Trouble Codes",
}


def sid_to_name(sid: int) -> Optional[str]:
    if sid in _sid_to_name:
        return _sid_to_name[sid]

    return None


# TODO: PIDs
