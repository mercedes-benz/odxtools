# SPDX-License-Identifier: MIT
import dataclasses
import re
from typing import Any, Dict


def dataclass_fields_asdict(obj: Any) -> Dict[str, Any]:
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
