# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the
    circumstances in which the error occurred.

    This is one of the many multiplexer mechanisms specified by the
    ODX standard, because an environment data parameter must only be
    used if a DTC parameter has a certain set of values. (In this
    sense, it is quite similar to NRC-CONST parameters.)
    """

    all_value: bool | None = None
    dtc_values: list[int] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EnvironmentData":
        """Reads Environment Data from Diag Layer."""
        kwargs = dataclass_fields_asdict(BasicStructure.from_et(et_element, context))

        all_value_elem = et_element.find("ALL-VALUE")
        all_value = None if all_value_elem is None else True
        dtc_values = [
            int(odxrequire(dtcv_elem.text))
            for dtcv_elem in et_element.iterfind("DTC-VALUES/DTC-VALUE")
        ]

        return EnvironmentData(all_value=all_value, dtc_values=dtc_values, **kwargs)
