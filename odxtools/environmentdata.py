# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment
from .odxtypes import odxstr_to_bool
from .parameters.createanyparameter import create_any_parameter_from_et
from .utils import dataclass_fields_asdict


@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    dtc_values: List[int]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EnvironmentData":
        """Reads Environment Data from Diag Layer."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
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
            parameters=NamedItemList(parameters),
            byte_size=byte_size,
            dtc_values=dtc_values,
            **kwargs)
