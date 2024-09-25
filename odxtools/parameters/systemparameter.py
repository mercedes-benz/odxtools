# SPDX-License-Identifier: MIT
import getpass
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..encodestate import EncodeState
from ..exceptions import odxraise, odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP

# The SYSTEM parameter types mandated by the ODX 2.2 standard. Users
# are free to specify additional types, but these must be handled
# (cf. table 5 in section 7.3.5.4 of the ASAM ODX 2.2 specification
# document.)
PREDEFINED_SYSPARAM_VALUES = [
    "TIMESTAMP", "SECOND", "MINUTE", "HOUR", "TIMEZONE", "DAY", "WEEK", "MONTH", "YEAR", "CENTURY",
    "TESTERID", "USERID"
]


@dataclass
class SystemParameter(ParameterWithDOP):
    sysparam: str

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SystemParameter":

        kwargs = dataclass_fields_asdict(ParameterWithDOP.from_et(et_element, doc_frags))

        sysparam = odxrequire(et_element.get("SYSPARAM"))

        return SystemParameter(sysparam=sysparam, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "SYSTEM"

    @property
    @override
    def is_required(self) -> bool:
        # if a SYSTEM parameter is not specified explicitly, its value
        # can be determined from the operating system if it is type is
        # predefined
        return self.sysparam not in PREDEFINED_SYSPARAM_VALUES

    @property
    @override
    def is_settable(self) -> bool:
        return True

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        if physical_value is None:
            # determine the value to be encoded automatically
            now = datetime.now()
            if self.sysparam == "TIMESTAMP":
                physical_value = round(now.timestamp() * 1000).to_bytes(8, "big")
            elif self.sysparam == "SECOND":
                physical_value = now.second
            elif self.sysparam == "MINUTE":
                physical_value = now.minute
            elif self.sysparam == "HOUR":
                physical_value = now.hour
            elif self.sysparam == "TIMEZONE":
                if (utc_offset := now.astimezone().utcoffset()) is not None:
                    physical_value = utc_offset.seconds // 60
                else:
                    physical_value = 0
            elif self.sysparam == "DAY":
                physical_value = now.day
            elif self.sysparam == "WEEK":
                physical_value = now.isocalendar()[1]
            elif self.sysparam == "MONTH":
                physical_value = now.month
            elif self.sysparam == "YEAR":
                physical_value = now.year
            elif self.sysparam == "CENTURY":
                physical_value = now.year // 100
            elif self.sysparam == "TESTERID":
                physical_value = "odxtools".encode("latin1")
            elif self.sysparam == "USERID":
                physical_value = getpass.getuser().encode("latin1")
            else:
                odxraise(f"Unknown system parameter type '{self.sysparam}'")
                physical_value = 0

        self.dop.encode_into_pdu(physical_value, encode_state=encode_state)
