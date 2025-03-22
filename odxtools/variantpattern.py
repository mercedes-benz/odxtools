# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Union
from xml.etree import ElementTree

from .exceptions import odxraise
from .matchingparameter import MatchingParameter
from .odxlink import OdxDocFragment

if TYPE_CHECKING:
    from .matchingbasevariantparameter import MatchingBaseVariantParameter
    from .matchingparameter import MatchingParameter


@dataclass
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
            self) -> Union[List["MatchingParameter"], List["MatchingBaseVariantParameter"]]:
        odxraise(
            f"VariantPattern subclass `{type(self).__name__}` does not "
            f"implement `.get_match_parameters()`", RuntimeError)
        return []

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "VariantPattern":
        return VariantPattern()
