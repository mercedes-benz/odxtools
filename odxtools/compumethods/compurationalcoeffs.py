# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from ..exceptions import odxassert, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxtypes import DataType


@dataclass(kw_only=True)
class CompuRationalCoeffs:
    value_type: DataType

    numerators: list[int | float]
    denominators: list[int | float]

    @staticmethod
    def coeffs_from_et(et_element: ElementTree.Element, context: OdxDocContext, *,
                       value_type: DataType) -> "CompuRationalCoeffs":
        odxassert(
            value_type
            in (DataType.A_UINT32, DataType.A_INT32, DataType.A_FLOAT32, DataType.A_FLOAT64),
            "Rational coefficients must be of numeric type.")

        numerators = [
            cast(float, value_type.from_string(odxrequire(elem.text)))
            for elem in et_element.iterfind("COMPU-NUMERATOR/V")
        ]
        denominators = [
            cast(float, value_type.from_string(odxrequire(elem.text)))
            for elem in et_element.iterfind("COMPU-DENOMINATOR/V")
        ]

        return CompuRationalCoeffs(
            value_type=value_type, numerators=numerators, denominators=denominators)
