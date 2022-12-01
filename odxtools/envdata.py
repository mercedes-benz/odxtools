# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any, Dict, List

from .parameters import read_parameter_from_odx
from .utils import read_description_from_odx
from .odxlink import OdxLinkId, OdxDocFragment, OdxLinkDatabase
from .structures import BasicStructure
from .parameters.parameterbase import Parameter
from .globals import logger

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 parameters: List[Parameter],
                 dtc_values: Optional[List[int]] = None,
                 long_name: Optional[str] = None,
                 description: Optional[str] = None) -> None:
        super().__init__(odx_id,
                         short_name,
                         parameters,
                         long_name=long_name,
                         description=description)
        self.dtc_values = dtc_values

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        odxlinks[self.odx_id] = self

        return odxlinks

    def _resolve_references(self,  # type: ignore[override]
                            parent_dl: "DiagLayer",
                            odxlinks: OdxLinkDatabase) \
            -> None:
        super()._resolve_references(parent_dl, odxlinks)

    def __repr__(self) -> str:
        return (
            f"EnvironmentData('{self.short_name}', "
            + ", ".join([f"odx_id='{self.odx_id}'", f"parameters='{self.parameters}'"])
            + ")"
        )


def read_env_data_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> EnvironmentData:
    """Reads Environment Data from Diag Layer."""
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.findtext("SHORT-NAME")
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    parameters = [
        read_parameter_from_odx(et_parameter, doc_frags)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    dtc_values = None
    if (dtcv_elems := et_element.find("DTC-VALUES")) is not None:
        dtc_values = [
            int(dtcv_elem.text)
            for dtcv_elem in dtcv_elems.iterfind("DTC-VALUE")
        ]

    return EnvironmentData(odx_id,
                           short_name,
                           parameters=parameters,
                           dtc_values=dtc_values,
                           long_name=long_name,
                           description=description)
