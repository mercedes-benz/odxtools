# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Dict, Literal, Optional, Any, Union, overload
from xml.etree import ElementTree

from .odxlink import OdxDocFragment

@overload
def str_to_bool(str_val: None) -> None: ...

@overload
def str_to_bool(str_val: str) -> bool: ...

def str_to_bool(str_val: Union[None, str]) -> Union[None, bool]:
    if str_val is None:
        return None

    str_val = str_val.strip()
    assert str_val in ["0", "1", "false", "true"]

    return str_val in ["1", "true"]

def bool_to_str(bool_val: bool) -> str:
    return "true" if bool_val else "false"

def create_description_from_et(et_element: Optional[ElementTree.Element]) \
 -> Optional[str]:
    """Read a description tag.

    The description is located underneath the DESC tag of an an ODX
    element."""

    if et_element is None:
        return None

    if et_element.tag != "DESC":
        raise TypeError(f"Attempted to extract an ODX description from a "
                        f"'{et_element.tag}' XML node. (Must be a 'DESC' node!)")

    # Extract the contents of the tag as a XHTML string.
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
