# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Dict, Literal
from xml.etree import ElementTree


def read_description_from_odx(et_element: ElementTree.Element):
    """Read a DESCRIPTION element. The element usually has the name DESC."""
    if et_element is None:
        return None

    raw_string = ElementTree.tostring(et_element,
                                      encoding="unicode",
                                      method="xml")
    # Remove DESC start and end tag.
    raw_string = "\n".join(raw_string.split("\n")[1:-2])
    return raw_string.strip()


def read_element_id(et_element) -> Dict[Literal["short_name", "long_name", "description"], str]:
    """Read the elements "SHORT-NAME", "LONG-NAME" and "DESCRIPTION".

    Returns the dict
    ```python
    {
        "short_name": et_element.find("SHORT-NAME"),
        "long_name": et_element.find("LONG-NAME"),
        "description": read_description_from_odx(et_element.find("DESC"))
    }
    ```
    If `et_element` does not contain the elements "LONG-NAME" and "DESC",
    the returned dict does not contain the correspondig keys.

    A typical use for this function is reading an odx element
    that contains the group "ELEMENT-ID", e.g.,
    ```python
    def read_type_with_element_id_from_odx(et_element):
        element_id = read_element_id(et_element)
        return TypeWithElementID(**element_id)
    ```

    """
    d: Dict[Literal["short_name", "long_name", "description"], str] = {
        "short_name": et_element.findtext("SHORT-NAME")
    }
    if et_element.find("LONG-NAME") is not None:
        d["long_name"] = et_element.findtext("LONG-NAME")
    if et_element.find("DESC") is not None:
        d["description"] = read_description_from_odx(et_element.find("DESC"))
    return d
