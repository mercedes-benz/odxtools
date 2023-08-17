# SPDX-License-Identifier: MIT
from dataclasses import asdict, dataclass
from typing import List
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment
from .odxtypes import odxstr_to_bool
from .parameters.createanyparameter import create_any_parameter_from_et


@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    dtc_values: List[int]

    def __init__(self, *, dtc_values: List[int], **kwargs):
        super().__init__(**kwargs)
        self.dtc_values = dtc_values

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EnvironmentData":
        """Reads Environment Data from Diag Layer."""
        kwargs = asdict(IdentifiableElement._from_et(et_element, doc_frags))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        parameters = [
            create_any_parameter_from_et(et_parameter, doc_frags)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ]
        byte_size_text = et_element.findtext("BYTE-SIZE")
        byte_size = None if byte_size_text is None else int(byte_size_text)
        dtc_values = [
            int(odxrequire(dtcv_elem.text))
            for dtcv_elem in et_element.iterfind("DTC-VALUES/DTC-VALUE")
        ]

        return EnvironmentData(
            sdgs=sdgs,
            is_visible_raw=is_visible_raw,
            parameters=parameters,
            byte_size=byte_size,
            dtc_values=dtc_values,
            **kwargs)
