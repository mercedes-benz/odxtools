# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxassert, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .physicaldimension import PhysicalDimension
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class Unit(IdentifiableElement):
    """
    A unit consists of an ID, short name and a display name.

    Additionally, a unit may reference an SI unit (`.physical_dimension`)
    and an offset to that unit (`factor_si_to_unit`, `offset_si_to_unit`).
    The factor and offset are defined such that the following equation holds true:

    UNIT = FACTOR-SI-TO-UNIT * SI-UNIT + OFFSET-SI-TO-UNIT

    For example: 1km = 1000 * 1m + 0

    Examples
    --------

    A minimal unit representing kilometres:

    ```
    Unit(
        odx_id="kilometre",
        short_name="kilometre",
        display_name="km"
    )
    ```

    A unit that also references a physical dimension:

    ```
    Unit(
        odx_id=OdxLinkId("ID.kilometre", doc_frags),
        short_name="Kilometre",
        display_name="km",
        physical_dimension_ref=OdxLinkRef("ID.metre", doc_frags),
        factor_si_to_unit=1000,
        offset_si_to_unit=0
    )
    # where the physical_dimension_ref references, e.g.:
    PhysicalDimension(odx_id=OdxLinkId("ID.metre", doc_frags), short_name="metre", length_exp=1)
    ```
    """
    display_name: str
    factor_si_to_unit: Optional[float]
    offset_si_to_unit: Optional[float]
    physical_dimension_ref: Optional[OdxLinkRef]

    def __post_init__(self) -> None:
        self._physical_dimension = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Unit":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        display_name = odxrequire(et_element.findtext("DISPLAY-NAME"))

        def read_optional_float(element: ElementTree.Element, name: str) -> Optional[float]:
            if (elem_str := element.findtext(name)) is not None:
                return float(elem_str)
            else:
                return None

        factor_si_to_unit = read_optional_float(et_element, "FACTOR-SI-TO-UNIT")
        offset_si_to_unit = read_optional_float(et_element, "OFFSET-SI-TO-UNIT")
        physical_dimension_ref = OdxLinkRef.from_et(
            et_element.find("PHYSICAL-DIMENSION-REF"), doc_frags)

        return Unit(
            display_name=display_name,
            factor_si_to_unit=factor_si_to_unit,
            offset_si_to_unit=offset_si_to_unit,
            physical_dimension_ref=physical_dimension_ref,
            **kwargs)

    @property
    def physical_dimension(self) -> Optional[PhysicalDimension]:
        return self._physical_dimension

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.physical_dimension_ref:
            self._physical_dimension = odxlinks.resolve(self.physical_dimension_ref)

            odxassert(
                isinstance(self._physical_dimension, PhysicalDimension),
                f"The physical_dimension_ref must be resolved to a PhysicalDimension."
                f" {self.physical_dimension_ref} referenced {self._physical_dimension}")

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
