# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass

from odxtools.parameters import read_parameter_from_odx

from odxtools.utils import read_description_from_odx

from odxtools.structures import BasicStructure

from .globals import logger


@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    def __init__(
        self,
        id,
        short_name,
        parameters,
        long_name=None,
        description=None,
    ):
        super().__init__(
            id, short_name, parameters, long_name=long_name, description=description
        )

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup.update({self.id: self})
        return id_lookup

    def __repr__(self) -> str:
        return (
            f"EnvironmentData('{self.short_name}', "
            + ", ".join([f"id='{self.id}'", f"parameters='{self.parameters}'"])
            + ")"
        )


def read_env_data_from_odx(et_element):
    """Reads Environment Data from Diag Layer."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    description = read_description_from_odx(et_element.find("DESC"))
    parameters = [
        read_parameter_from_odx(et_parameter)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    logger.debug("Parsing ENV-DATA " + short_name)

    env_data = EnvironmentData(
        id,
        short_name,
        parameters=parameters,
        long_name=long_name,
        description=description,
    )

    return env_data
