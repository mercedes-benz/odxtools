# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import re
from typing import Any, Optional
from xml.etree import ElementTree


def create_description_from_et(et_element: Optional[ElementTree.Element],) -> Optional[str]:
    """Read a description tag.

    The description is located underneath the DESC tag of an an ODX
    element."""

    if et_element is None:
        return None

    if et_element.tag != "DESC":
        raise TypeError(f"Attempted to extract an ODX description from a "
                        f"'{et_element.tag}' XML node. (Must be a 'DESC' node!)")

    # Extract the contents of the tag as a XHTML string.
    raw_string = et_element.text or ""
    for e in et_element:
        raw_string += ElementTree.tostring(e, encoding="unicode")

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


# ISO 22901 section 7.1.1
_short_name_pattern = re.compile("[a-zA-Z0-9_]+")
# ISO 22901 section 7.3.13.3
_short_name_path_pattern = re.compile("[a-zA-Z0-9_]+(.[a-zA-Z0-9_]+)*")


def is_short_name(test_val: str) -> bool:
    """Returns true iff the test_val string is a ODX short name.

    See also: ISO 22901 section 7.1.1
    """
    return _short_name_pattern.fullmatch(test_val) is not None


def is_short_name_path(test_val: str) -> bool:
    """Returns true iff the test_val string is a ODX short name path.

    See also: ISO 22901 section 7.3.13.3
    """
    return _short_name_path_pattern.fullmatch(test_val) is not None
