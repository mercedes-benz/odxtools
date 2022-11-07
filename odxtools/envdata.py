# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Any, Dict, List

from .parameters import read_parameter_from_odx
from .utils import read_description_from_odx
from .odxlink import OdxLinkId, OdxDocFragment
from .structures import BasicStructure
from .globals import logger

@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    def __init__(
        self,
        odx_id,
        short_name,
        parameters,
        long_name=None,
        description=None,
    ):
        super().__init__(
            odx_id, short_name, parameters, long_name=long_name, description=description
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}
        return odxlinks

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
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    description = read_description_from_odx(et_element.find("DESC"))
    parameters = [
        read_parameter_from_odx(et_parameter, doc_frags)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    logger.debug("Parsing ENV-DATA " + short_name)

    env_data = EnvironmentData(
        odx_id,
        short_name,
        parameters=parameters,
        long_name=long_name,
        description=description,
    )

    return env_data
