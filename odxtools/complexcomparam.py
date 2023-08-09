# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .utils import short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

ComplexValue = List[Union[str, "ComplexValue"]]


def create_complex_value_from_et(et_element: ElementTree.Element) -> ComplexValue:
    result: ComplexValue = []
    for el in et_element:
        if el.tag == "SIMPLE-VALUE":
            result.append("" if el.text is None else el.text)
        else:
            result.append(create_complex_value_from_et(el))
    return result


@dataclass
class ComplexComparam(BaseComparam):
    comparams: NamedItemList[BaseComparam]
    complex_physical_default_value: Optional[ComplexValue]
    allow_multiple_values_raw: Optional[bool]

    @property
    def allow_multiple_values(self) -> bool:
        return self.allow_multiple_values_raw == True

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ComplexComparam":
        # create an "empty" ComplexComparam object without calling the
        # "official" constructor. We need to do this because we need
        # all data attributes of the class to call the constructor,
        # including those which are supposed to be handled by the base
        # class (i.e., ComparamBase)
        result = ComplexComparam.__new__(ComplexComparam)

        # initialize the new "empty" object from the ElementTree
        result.__init_from_et__(et_element, doc_frags)

        return result

    def __init_from_et__(self, et_element: ElementTree.Element,
                         doc_frags: List[OdxDocFragment]) -> None:
        super().__init_from_et__(et_element, doc_frags)

        # to avoid a cyclic import, create_any_comparam_from_et cannot
        # be imported globally. TODO: figure out if this has
        # performance implications
        from .createanycomparam import create_any_comparam_from_et

        self.comparams = NamedItemList(short_name_as_id)
        for cp_el in et_element:
            if cp_el.tag in ("COMPARAM", "COMPLEX-COMPARAM"):
                self.comparams.append(create_any_comparam_from_et(cp_el, doc_frags))

        self.complex_physical_default_value = None
        if cpdv_elem := et_element.find("COMPLEX-PHYSICAL-DEFAULT-VALUE"):
            self.complex_physical_default_value = create_complex_value_from_et(cpdv_elem)

        self.allow_multiple_values_raw = odxstr_to_bool(et_element.get("ALLOW-MULTIPLE-VALUES"))

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)
        for comparam in self.comparams:
            comparam._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)
        for comparam in self.comparams:
            comparam._resolve_snrefs(diag_layer)
