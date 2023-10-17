# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from deprecation import deprecated

from .odxtypes import ParameterValue, ParameterValueDict

if TYPE_CHECKING:
    from .diagservice import DiagService
    from .request import Request
    from .response import Response


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
    coding_object: Union["Request", "Response"]
    param_dict: ParameterValueDict

    def __getitem__(self, key: str) -> ParameterValue:
        return self.param_dict[key]

    @property
    @deprecated("use .coding_object")
    def structure(self) -> Union["Request", "Response"]:
        return self.coding_object
