# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Optional
from odxtools.utils import read_description_from_odx


@dataclass()
class State:
    """
    Corresponds to STATE.
    """
    id: str
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None


def read_state_from_odx(et_element):
    short_name = et_element.findtext("SHORT-NAME")
    id = et_element.get("ID")

    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    return State(id=id,
                 short_name=short_name,
                 long_name=long_name,
                 description=description)
