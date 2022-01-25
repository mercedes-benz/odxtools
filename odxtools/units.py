# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Union

from .nameditemlist import NamedItemList
from .utils import read_description_from_odx

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
        id="velocity",
        short_name="metre_per_second",
        length_exp=1,
        time_exp=-1
    )
    ```
    """
    id: str
    short_name: str
    oid: Optional[str] = None
    long_name: Optional[str] = None
    description: Optional[str] = None
    length_exp: int = 0
    mass_exp: int = 0
    time_exp: int = 0
    current_exp: int = 0
    temperature_exp: int = 0
    molar_amount_exp: int = 0
    luminous_intensity_exp: int = 0


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
        id="kilometre",
        short_name="kilometre",
        display_name="km"
    )
    ```

    A unit that also references a physical dimension:

    ```
    Unit(
        id="ID.kilometre",
        short_name="Kilometre",
        display_name="km",
        physical_dimension_ref="ID.metre",
        factor_si_to_unit=1000,
        offset_si_to_unit=0
    )
    # where the physical_dimension_ref references, e.g.:
    PhysicalDimension(id="ID.metre", short_name="metre", length_exp=1)
    ```
    """
    id: str
    short_name: str
    display_name: str
    oid: Optional[str] = None
    long_name: Optional[str] = None
    description: Optional[str] = None
    factor_si_to_unit: Optional[float] = None
    offset_si_to_unit: Optional[float] = None
    physical_dimension_ref: Optional[str] = None

    def __post_init__(self):
        self._physical_dimension = None

        if self.factor_si_to_unit is not None or self.offset_si_to_unit is not None or self.physical_dimension_ref is not None:
            assert self.factor_si_to_unit is not None and self.offset_si_to_unit is not None and self.physical_dimension_ref is not None, (
                f"Error 54: If one of factor_si_to_unit, offset_si_to_unit and physical_dimension_ref is defined,"
                f" all of them must be defined: {self.factor_si_to_unit} and {self.offset_si_to_unit} and {self.physical_dimension_ref}"
            )

    @property
    def physical_dimension(self) -> PhysicalDimension:
        return self._physical_dimension

    def _resolve_references(self, id_lookup):
        if self.physical_dimension_ref:
            self._physical_dimension = id_lookup[self.physical_dimension_ref]

            assert isinstance(self._physical_dimension, PhysicalDimension), (
                f"The physical_dimension_ref must be resolved to a PhysicalDimension."
                f" {self.physical_dimension_ref} referenced {self._physical_dimension}"
            )


@dataclass
class UnitGroup:
    """A group of units.

    There are two categories of groups: COUNTRY and EQUIV-UNITS.
    """
    short_name: str
    category: UnitGroupCategory
    unit_refs: List[str] = field(default_factory=list)
    oid: Optional[str] = None
    long_name: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        self._units = NamedItemList[Unit](lambda unit: unit.short_name)

    def _resolve_references(self, id_lookup):
        self._units = NamedItemList[Unit](
            lambda unit: unit.short_name,
            [id_lookup[ref] for ref in self.unit_refs]
        )

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
    unit_groups: Union[NamedItemList[UnitGroup],
                       List[UnitGroup]] = field(default_factory=list)  # type: ignore
    units: Union[NamedItemList[Unit], List[Unit]] = field(
        default_factory=list)  # type: ignore
    physical_dimensions: Union[NamedItemList[PhysicalDimension],
                               List[PhysicalDimension]] = field(default_factory=list)  # type: ignore

    def __post_init__(self):
        self.unit_groups = NamedItemList(lambda x: x.short_name,
                                         self.unit_groups)
        self.units = NamedItemList(lambda x: x.short_name, self.units)
        self.physical_dimensions = NamedItemList(lambda x: x.short_name,
                                                 self.physical_dimensions)

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup.update({
            unit.id: unit for unit in self.units
        })
        id_lookup.update({
            dim.id: dim for dim in self.physical_dimensions
        })
        return id_lookup

    def _resolve_references(self, id_lookup):
        for unit in self.units:
            unit._resolve_references(id_lookup)
        for group in self.unit_groups:
            group._resolve_references(id_lookup)


def read_unit_from_odx(et_element):
    id = et_element.get("ID")
    oid = et_element.get("OID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    display_name = et_element.find("DISPLAY-NAME").text

    def read_optional_float(element, name):
        if element.findtext(name):
            return float(element.findtext(name))
        else:
            return None
    factor_si_to_unit = read_optional_float(et_element, "FACTOR-SI-TO-UNIT")
    offset_si_to_unit = read_optional_float(et_element, "OFFSET-SI-TO-UNIT")

    ref_element = et_element.find("PHYSICAL-DIMENSION-REF")
    if ref_element is not None:
        physical_dimension_ref = ref_element.get("ID-REF")
    else:
        physical_dimension_ref = None

    return Unit(
        id=id,
        short_name=short_name,
        display_name=display_name,
        oid=oid,
        long_name=long_name,
        description=description,
        factor_si_to_unit=factor_si_to_unit,
        offset_si_to_unit=offset_si_to_unit,
        physical_dimension_ref=physical_dimension_ref
    )


def read_physical_dimension_from_odx(et_element):
    id = et_element.get("ID")
    oid = et_element.get("OID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    def read_optional_int(element, name):
        if element.findtext(name):
            return int(element.findtext(name))
        else:
            return 0

    length_exp = read_optional_int(et_element, "LENGTH-EXP")
    mass_exp = read_optional_int(et_element, "MASS-EXP")
    time_exp = read_optional_int(et_element, "TIME-EXP")
    current_exp = read_optional_int(et_element, "CURRENT-EXP")
    temperature_exp = read_optional_int(et_element, "TEMPERATURE-EXP")
    molar_amount_exp = read_optional_int(et_element, "MOLAR-AMOUNT-EXP")
    luminous_intensity_exp = read_optional_int(et_element,
                                               "LUMINOUS-INTENSITY-EXP")

    return PhysicalDimension(
        id=id,
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
        luminous_intensity_exp=luminous_intensity_exp
    )


def read_unit_group_from_odx(et_element):
    oid = et_element.get("OID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    category = et_element.findtext("CATEGORY")
    assert category in [
        "COUNTRY", "EQUIV-UNITS"], f'A UNIT-GROUP-CATEGORY must be "COUNTRY" or "EQUIV-UNITS". It was {category}.'
    unit_refs = [el.get("ID-REF")
                 for el in et_element.iterfind("UNIT-REFS/UNIT-REF")]

    return UnitGroup(
        short_name=short_name,
        category=category,
        unit_refs=unit_refs,
        oid=oid,
        long_name=long_name,
        description=description
    )


def read_unit_spec_from_odx(et_element):

    unit_groups = [read_unit_group_from_odx(el)
                   for el in et_element.iterfind("UNIT-GROUPS/UNIT-GROUP")]
    units = [read_unit_from_odx(el)
             for el in et_element.iterfind("UNITS/UNIT")]
    physical_dimensions = [read_physical_dimension_from_odx(el)
                           for el in et_element.iterfind("PHYSICAL-DIMENSIONS/PHYSICAL-DIMENSION")]
    return UnitSpec(
        unit_groups=unit_groups,
        units=units,
        physical_dimensions=physical_dimensions
    )
