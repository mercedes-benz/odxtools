# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .physicaldimension import PhysicalDimension
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
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
    factor_si_to_unit: float | None = None
    offset_si_to_unit: float | None = None
    physical_dimension_ref: OdxLinkRef | None = None

    @property
    def physical_dimension(self) -> PhysicalDimension | None:
        return self._physical_dimension

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Unit":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        display_name = odxrequire(et_element.findtext("DISPLAY-NAME"))

        def read_optional_float(element: ElementTree.Element, name: str) -> float | None:
            if (elem_str := element.findtext(name)) is not None:
                return float(elem_str)
            else:
                return None

        factor_si_to_unit = read_optional_float(et_element, "FACTOR-SI-TO-UNIT")
        offset_si_to_unit = read_optional_float(et_element, "OFFSET-SI-TO-UNIT")
        physical_dimension_ref = OdxLinkRef.from_et(
            et_element.find("PHYSICAL-DIMENSION-REF"), context)

        return Unit(
            display_name=display_name,
            factor_si_to_unit=factor_si_to_unit,
            offset_si_to_unit=offset_si_to_unit,
            physical_dimension_ref=physical_dimension_ref,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._physical_dimension: PhysicalDimension | None = None
        if self.physical_dimension_ref:
            self._physical_dimension = odxlinks.resolve(self.physical_dimension_ref,
                                                        PhysicalDimension)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
