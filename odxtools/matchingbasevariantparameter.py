# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .matchingparameter import MatchingParameter
from .odxdoccontext import OdxDocContext
from .odxtypes import odxstr_to_bool
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class MatchingBaseVariantParameter(MatchingParameter):
    """A description of a parameter used for base variant matching.

    This is very similar to `MatchingParameter` for ECU variant
    matching, but `MatchingBaseVariantParameter` features the
    additional subtag `USE-PHYSICAL-ADDRESSING`.
    """

    use_physical_addressing_raw: bool | None = None

    @property
    def use_physical_addressing(self) -> bool:
        return self.use_physical_addressing_raw in [None, True]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "MatchingBaseVariantParameter":

        kwargs = dataclass_fields_asdict(MatchingParameter.from_et(et_element, context))

        use_physical_addressing_raw = odxstr_to_bool(et_element.findtext("USE-PHYSICAL-ADDRESSING"))

        return MatchingBaseVariantParameter(
            use_physical_addressing_raw=use_physical_addressing_raw,
            **kwargs,
        )
