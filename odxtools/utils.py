# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Dict, Literal, Optional, Any
from xml.etree import ElementTree

from .odxlink import OdxDocFragment

def read_description_from_odx(et_element: Optional[ElementTree.Element]) \
 -> Optional[str]:
    """Read a description of an XML element.

    The description is located underneath the DESC sub-tag."""

    # TODO: Invent a better representation of a DESC element.
    #       This just represents it as XHTML string.
    if et_element is None:
        return None

    if et_element.tag != "DESC":
        raise TypeError(f"Attempted to extract ODX desctiption from "
                        f"{et_element.tag} XML node. (Must be a DESC node!)")

    raw_string = et_element.text or ''
    for e in et_element:
        raw_string += ElementTree.tostring(e, encoding='unicode')

    return raw_string.strip()


def short_name_as_id(obj: Any) -> str:
    """Retrieve an object's `short_name` attribute into a valid python identifier.

    Although short names are almost identical to python identifiers,
    their first character is allowed to be a number. This method
    prepends an underscore to such such shortnames.
    """

    sn = obj.short_name
    assert isinstance(sn, str)

    if sn[0].isdigit():
        return f"_{sn}"

    return sn
