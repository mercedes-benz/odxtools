# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING
from xml.etree import ElementTree

from .exceptions import odxraise
from .matchingparameter import MatchingParameter
from .odxdoccontext import OdxDocContext

if TYPE_CHECKING:
    from .matchingbasevariantparameter import MatchingBaseVariantParameter
    from .matchingparameter import MatchingParameter


@dataclass(kw_only=True)
class VariantPattern:
    """Variant patterns are used to identify the concrete variant of an ECU

    This is done by observing the responses after sending it some
    requests. There are two kinds of variant patterns:
    `BaseVariantPattern`s which are used to identify the applicable
    base variant and ECU variant patterns which can be used identify
    concrete revisions of the ECU in question. (Both types of pattern
    are optional, i.e., it might not be possible to identify the base-
    or ECU variant present.)
    """

    def get_matching_parameters(
            self) -> list["MatchingParameter"] | list["MatchingBaseVariantParameter"]:
        odxraise(
            f"VariantPattern subclass `{type(self).__name__}` does not "
            f"implement `.get_match_parameters()`", RuntimeError)
        return []

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "VariantPattern":
        return VariantPattern()
