# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .globals import logger
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .parameters import create_any_parameter_from_et
from .parameters.parameterbase import Parameter
from .specialdata import create_sdgs_from_et
from .structures import BasicStructure
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    dtc_values: List[int]

    def __init__(self, *, dtc_values: List[int], **kwargs):
        super().__init__(**kwargs)
        self.dtc_values = dtc_values

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "EnvironmentData":
        """Reads Environment Data from Diag Layer."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        parameters = [
            create_any_parameter_from_et(et_parameter, doc_frags)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ]
        byte_size_text = et_element.findtext("BYTE-SIZE")
        byte_size = None if byte_size_text is None else int(byte_size_text)
        dtc_values = [
            int(dtcv_elem.text) for dtcv_elem in et_element.iterfind("DTC-VALUES/DTC-VALUE")
        ]

        return EnvironmentData(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            sdgs=sdgs,
            is_visible_raw=is_visible_raw,
            parameters=parameters,
            byte_size=byte_size,
            dtc_values=dtc_values,
        )

    def __repr__(self) -> str:
        return (f"EnvironmentData('{self.short_name}', " +
                ", ".join([f"odx_id='{self.odx_id}'", f"parameters='{self.parameters}'"]) + ")")
