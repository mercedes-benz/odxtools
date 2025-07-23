# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class PhysicalDimension(IdentifiableElement):
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
    length_exp: int | None = None
    mass_exp: int | None = None
    time_exp: int | None = None
    current_exp: int | None = None
    temperature_exp: int | None = None
    molar_amount_exp: int | None = None
    luminous_intensity_exp: int | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "PhysicalDimension":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        def read_optional_int(element: ElementTree.Element, name: str) -> int | None:
            if (val_str := element.findtext(name)) is not None:
                return int(val_str)
            else:
                return None

        length_exp = read_optional_int(et_element, "LENGTH-EXP")
        mass_exp = read_optional_int(et_element, "MASS-EXP")
        time_exp = read_optional_int(et_element, "TIME-EXP")
        current_exp = read_optional_int(et_element, "CURRENT-EXP")
        temperature_exp = read_optional_int(et_element, "TEMPERATURE-EXP")
        molar_amount_exp = read_optional_int(et_element, "MOLAR-AMOUNT-EXP")
        luminous_intensity_exp = read_optional_int(et_element, "LUMINOUS-INTENSITY-EXP")

        return PhysicalDimension(
            length_exp=length_exp,
            mass_exp=mass_exp,
            time_exp=time_exp,
            current_exp=current_exp,
            temperature_exp=temperature_exp,
            molar_amount_exp=molar_amount_exp,
            luminous_intensity_exp=luminous_intensity_exp,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
