# SPDX-License-Identifier: MIT
import dataclasses
import re
from typing import TYPE_CHECKING, Any, Optional
from xml.etree import ElementTree

from .exceptions import odxraise

if TYPE_CHECKING:
    from .database import Database
    from .diaglayers.diaglayer import DiagLayer
    from .snrefcontext import SnRefContext


def read_hex_binary(et_element: ElementTree.Element | None) -> int | None:
    """Convert the contents of an xsd:hexBinary to an integer
    """
    if et_element is None:
        return None

    if (bytes_str := et_element.text) is None:
        # tag exists but is immediately terminated ("<FOO />"). we
        # treat this like an empty string.
        return 0

    # The XSD uses the type xsd:hexBinary and xsd:hexBinary allows for
    # leading/trailing whitespace and empty strings whilst `int(x,
    # 16)` raises an exception if one of these things happen.
    bytes_str = bytes_str.strip()
    if len(bytes_str) == 0:
        return 0

    try:
        return int(bytes_str, 16)
    except Exception as e:
        odxraise(f"Caught exception while parsing hex string `{bytes_str}`"
                 f" of {et_element.tag}: {e}")
        return None


def retarget_snrefs(database: "Database",
                    diag_layer: "DiagLayer",
                    context: Optional["SnRefContext"] = None) -> None:
    """Re-resolve the short name references reachable by a
    DiagLayer to this DiagLayer

    This implies that after the SNREFs have been retargeted, accessing
    the resolved objects via a different diagnostic layer might not be
    correct. E.g.: If the ECU variants "V1" and "V2" are derived from
    the base variant "BV", BV defines a short name reference to a data
    object property called "Foo" and V1 and V2 both define a "Foo"
    DOP, the reference in the base variant to Foo ought to be resolved
    differently depending on whether it is accessed via V1 or
    V2. Since odxtools resolves all references ahead of time, a fixed
    variant has to be chosen. This method allows to switch the variant
    to another one.

    """
    from .snrefcontext import SnRefContext

    if context is None:
        context = SnRefContext()

    if context.database is None:
        context.database = database

    if context.diag_layer is None:
        context.diag_layer = diag_layer

    # retarget the objects "owned" by the layer itself
    diag_layer._resolve_snrefs(context)

    # retarget all parents of the current layer (if any)
    if (parent_refs := getattr(diag_layer, "parent_refs", None)) is not None:
        for pr in parent_refs:
            retarget_snrefs(database, pr.layer, context)


def dataclass_fields_asdict(obj: Any) -> dict[str, Any]:
    """Extract all attributes from a dataclass object that are fields.

    This is a non-recursive version of `dataclasses.asdict()`. Its
    purpose is to make hierarchies of dataclasses possible while
    initializing the base class using common code.

    """
    return {x.name: getattr(obj, x.name) for x in dataclasses.fields(obj)}


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
