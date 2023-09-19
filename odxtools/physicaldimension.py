# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .element import IdentifiableElement
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
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
    oid: Optional[str]
    length_exp: int
    mass_exp: int
    time_exp: int
    current_exp: int
    temperature_exp: int
    molar_amount_exp: int
    luminous_intensity_exp: int

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "PhysicalDimension":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        oid = et_element.get("OID")

        def read_optional_int(element: ElementTree.Element, name: str) -> int:
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
            oid=oid,
            length_exp=length_exp,
            mass_exp=mass_exp,
            time_exp=time_exp,
            current_exp=current_exp,
            temperature_exp=temperature_exp,
            molar_amount_exp=molar_amount_exp,
            luminous_intensity_exp=luminous_intensity_exp,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
