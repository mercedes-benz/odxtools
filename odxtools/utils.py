# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

from xml.etree import ElementTree

def read_description_from_odx(et_element):
    """Read a DESCRIPTION element. The element usually has the name DESC."""
    if et_element is None:
        return None
    raw_string = ElementTree.tostring(et_element, encoding="unicode", method="xml")
    raw_string = "\n".join(raw_string.split("\n")[1:-2]) # Remove DESC start and end tag.
    return raw_string