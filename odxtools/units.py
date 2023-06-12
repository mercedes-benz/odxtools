# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

UnitGroupCategory = Literal["COUNTRY", "EQUIV-UNITS"]


@dataclass
class PhysicalDimension:
    """A physical dimension is a formal definition of a unit.

    It consists of the exponents for the SI units:

    | Symbol | Name     | Quantity                  | Property                 |
    |  ---   | ---      | ---                       | ---                      |
    | s      | second   | time                      | `time_exp`               |
    | m      | metre    | length                    | `length_exp`             |
    | kg     | kilogram | mass                      | `mass_exp`               |
    | A      | ampere   | electric current          | `current_exp`            |
    | K      | kelvin   | thermodynamic temperature | `temperature_exp`        |
    | mol    | mole     | amount of substance       | `molar_amount_exp`       |
    | cd     | candela  | luminous intensity        | `luminous_intensity_exp` |

    (The first three columns are from https://en.wikipedia.org/wiki/International_System_of_Units.)


    Examples
    --------

    The unit `m/s` (or `m**1 * s**(-1)`) can be represented as
    ```
    PhysicalDimension(
        odx_id="velocity",
        short_name="metre_per_second",
        length_exp=1,
        time_exp=-1
    )
    ```
    """

    odx_id: OdxLinkId
    short_name: str
    oid: Optional[str]
    long_name: Optional[str]
    description: Optional[str]
    length_exp: int
    mass_exp: int
    time_exp: int
    current_exp: int
    temperature_exp: int
    molar_amount_exp: int
    luminous_intensity_exp: int

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "PhysicalDimension":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        oid = et_element.get("OID")
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        def read_optional_int(element, name):
            if val_str := element.findtext(name):
                return int(val_str)
            else:
                return 0

        length_exp = read_optional_int(et_element, "LENGTH-EXP")
        mass_exp = read_optional_int(et_element, "MASS-EXP")
        time_exp = read_optional_int(et_element, "TIME-EXP")
        current_exp = read_optional_int(et_element, "CURRENT-EXP")
        temperature_exp = read_optional_int(et_element, "TEMPERATURE-EXP")
        molar_amount_exp = read_optional_int(et_element, "MOLAR-AMOUNT-EXP")
        luminous_intensity_exp = read_optional_int(et_element, "LUMINOUS-INTENSITY-EXP")

        return PhysicalDimension(
            odx_id=odx_id,
            short_name=short_name,
            oid=oid,
            long_name=long_name,
            description=description,
            length_exp=length_exp,
            mass_exp=mass_exp,
            time_exp=time_exp,
            current_exp=current_exp,
            temperature_exp=temperature_exp,
            molar_amount_exp=molar_amount_exp,
            luminous_intensity_exp=luminous_intensity_exp,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class Unit:
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

    odx_id: OdxLinkId
    short_name: str
    display_name: str
    oid: Optional[str]
    long_name: Optional[str]
    description: Optional[str]
    factor_si_to_unit: Optional[float]
    offset_si_to_unit: Optional[float]
    physical_dimension_ref: Optional[OdxLinkRef]

    def __post_init__(self):
        self._physical_dimension = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "Unit":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        oid = et_element.get("OID")
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        display_name = et_element.findtext("DISPLAY-NAME")

        def read_optional_float(element, name):
            if element.findtext(name):
                return float(element.findtext(name))
            else:
                return None

        factor_si_to_unit = read_optional_float(et_element, "FACTOR-SI-TO-UNIT")
        offset_si_to_unit = read_optional_float(et_element, "OFFSET-SI-TO-UNIT")
        physical_dimension_ref = OdxLinkRef.from_et(
            et_element.find("PHYSICAL-DIMENSION-REF"), doc_frags)

        return Unit(
            odx_id=odx_id,
            short_name=short_name,
            display_name=display_name,
            oid=oid,
            long_name=long_name,
            description=description,
            factor_si_to_unit=factor_si_to_unit,
            offset_si_to_unit=offset_si_to_unit,
            physical_dimension_ref=physical_dimension_ref,
        )

    @property
    def physical_dimension(self) -> PhysicalDimension:
        return self._physical_dimension

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.physical_dimension_ref:
            self._physical_dimension = odxlinks.resolve(self.physical_dimension_ref)

            assert isinstance(self._physical_dimension, PhysicalDimension), (
                f"The physical_dimension_ref must be resolved to a PhysicalDimension."
                f" {self.physical_dimension_ref} referenced {self._physical_dimension}")

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class UnitGroup:
    """A group of units.

    There are two categories of groups: COUNTRY and EQUIV-UNITS.
    """

    short_name: str
    category: UnitGroupCategory
    unit_refs: List[OdxLinkRef]
    oid: Optional[str]
    long_name: Optional[str]
    description: Optional[str]

    def __post_init__(self):
        self._units = NamedItemList[Unit](short_name_as_id)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "UnitGroup":
        oid = et_element.get("OID")
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        category = et_element.findtext("CATEGORY")
        assert category in [
            "COUNTRY",
            "EQUIV-UNITS",
        ], f'A UNIT-GROUP-CATEGORY must be "COUNTRY" or "EQUIV-UNITS". It was {category}.'
        unit_refs = []

        for el in et_element.iterfind("UNIT-REFS/UNIT-REF"):
            ref = OdxLinkRef.from_et(el, doc_frags)
            assert isinstance(ref, OdxLinkRef)
            unit_refs.append(ref)

        return UnitGroup(
            short_name=short_name,
            category=category,
            unit_refs=unit_refs,
            oid=oid,
            long_name=long_name,
            description=description,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._units = NamedItemList[Unit](short_name_as_id,
                                          [odxlinks.resolve(ref) for ref in self.unit_refs])

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def units(self) -> NamedItemList[Unit]:
        return self._units


@dataclass
class UnitSpec:
    """
    A unit spec encapsulates three lists:

    * unit groups
    * units
    * physical_dimensions

    The following odx elements are not internalized: ADMIN-DATA, SDGS
    """

    # TODO (?): Why are there type errors...
    unit_groups: Union[NamedItemList[UnitGroup], List[UnitGroup]]
    units: Union[NamedItemList[Unit], List[Unit]]
    physical_dimensions: Union[NamedItemList[PhysicalDimension], List[PhysicalDimension]]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self):
        self.unit_groups = NamedItemList(short_name_as_id, self.unit_groups)
        self.units = NamedItemList(short_name_as_id, self.units)
        self.physical_dimensions = NamedItemList(short_name_as_id, self.physical_dimensions)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]):

        unit_groups = [
            UnitGroup.from_et(el, doc_frags) for el in et_element.iterfind("UNIT-GROUPS/UNIT-GROUP")
        ]
        units = [Unit.from_et(el, doc_frags) for el in et_element.iterfind("UNITS/UNIT")]
        physical_dimensions = [
            PhysicalDimension.from_et(el, doc_frags)
            for el in et_element.iterfind("PHYSICAL-DIMENSIONS/PHYSICAL-DIMENSION")
        ]
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return UnitSpec(
            unit_groups=unit_groups,
            units=units,
            physical_dimensions=physical_dimensions,
            sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        for unit in self.units:
            odxlinks.update(unit._build_odxlinks())
        for dim in self.physical_dimensions:
            odxlinks.update(dim._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for unit in self.units:
            unit._resolve_odxlinks(odxlinks)
        for group in self.unit_groups:
            group._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for unit in self.units:
            unit._resolve_snrefs(diag_layer)
        for group in self.unit_groups:
            group._resolve_snrefs(diag_layer)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
