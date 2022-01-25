# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Optional
from odxtools.utils import read_description_from_odx


@dataclass()
class FunctionalClass:
    """
    Corresponds to FUNCT-CLASS.
    """
    id: str
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None


def read_functional_class_from_odx(et_element):
    short_name = et_element.find("SHORT-NAME").text
    id = et_element.get("ID")

    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    description = read_description_from_odx(et_element.find("DESC"))

    return FunctionalClass(id=id,
                           short_name=short_name,
                           long_name=long_name,
                           description=description)
