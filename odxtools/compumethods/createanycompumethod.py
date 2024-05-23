# SPDX-License-Identifier: MIT
from typing import List
from xml.etree import ElementTree

from ..exceptions import odxraise, odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import DataType
from .compumethod import CompuMethod
from .identicalcompumethod import IdenticalCompuMethod
from .linearcompumethod import LinearCompuMethod
from .scalelinearcompumethod import ScaleLinearCompuMethod
from .tabintpcompumethod import TabIntpCompuMethod
from .texttablecompumethod import TexttableCompuMethod


def create_any_compu_method_from_et(et_element: ElementTree.Element,
                                    doc_frags: List[OdxDocFragment], *, internal_type: DataType,
                                    physical_type: DataType) -> CompuMethod:
    compu_category = odxrequire(et_element.findtext("CATEGORY"))

    if compu_category == "IDENTICAL":
        return IdenticalCompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
    elif compu_category == "LINEAR":
        return LinearCompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
    elif compu_category == "SCALE-LINEAR":
        return ScaleLinearCompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
    elif compu_category == "TEXTTABLE":
        return TexttableCompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
    elif compu_category == "TAB-INTP":
        return TabIntpCompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)

    # TODO: Implement all categories (never instantiate the CompuMethod base class!)
    odxraise(f"Warning: Computation category {compu_category} is not implemented!")

    return IdenticalCompuMethod(internal_type=DataType.A_UINT32, physical_type=DataType.A_UINT32)
