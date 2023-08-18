# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING

from .odxtypes import ParameterValue, ParameterValueDict

if TYPE_CHECKING:
    from .diagservice import DiagService
    from .structure import Structure


class Message:
    """A diagnostic message with its interpretation.

    The `coded_message` attribute contains the binary data that's send
    over the wire using ISO-TP (CAN/LIN) or DoIP (Ethernet), while the
    remaining attributes of the class specify the "human readable"
    interpretation of the same data.
    """

    def __init__(self, *, coded_message: bytes, service: "DiagService", structure: "Structure",
                 param_dict: ParameterValueDict) -> None:
        self.coded_message = coded_message
        self.service = service
        self.structure = structure
        self.param_dict = param_dict

    def __getitem__(self, key: str) -> ParameterValue:
        return self.param_dict[key]

    def __str__(self) -> str:
        param_string = ", ".join(
            map(lambda param: f"{param[0]}={repr(param[1])}", self.param_dict.items()))
        return f"{self.structure.short_name}({param_string})"

    def __repr__(self) -> str:
        return self.__str__()
