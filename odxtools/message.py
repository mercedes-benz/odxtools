# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .odxtypes import ParameterValue, ParameterValueDict

if TYPE_CHECKING:
    from .diagservice import DiagService
    from .structure import Structure


@dataclass
class Message:
    """A diagnostic message with its interpretation.

    The `coded_message` attribute contains the binary data that's send
    over the wire using ISO-TP (CAN/LIN) or DoIP (Ethernet), while the
    remaining attributes of the class specify the "human readable"
    interpretation of the same data.
    """

    coded_message: bytes
    service: "DiagService"
    structure: "Structure"
    param_dict: ParameterValueDict

    def __getitem__(self, key: str) -> ParameterValue:
        return self.param_dict[key]
