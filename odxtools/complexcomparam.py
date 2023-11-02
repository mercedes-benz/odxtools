# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .utils import dataclass_fields_asdict

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
    subparams: NamedItemList[BaseComparam]
    physical_default_value: Optional[ComplexValue]
    allow_multiple_values_raw: Optional[bool]

    @property
    def allow_multiple_values(self) -> bool:
        return self.allow_multiple_values_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ComplexComparam":
        kwargs = dataclass_fields_asdict(BaseComparam.from_et(et_element, doc_frags))

        # to avoid a cyclic import, create_any_comparam_from_et cannot
        # be imported globally. TODO: figure out if this has
        # performance implications
        from .createanycomparam import create_any_comparam_from_et

        # extract the specifications of the sub-parameters and their
        # default values. Due to the quirky way this is defined by the
        # ODX specification, this is a *major* pain in the butt!
        subparams: NamedItemList[BaseComparam] = NamedItemList()
        elem_it = iter(et_element)
        while True:
            try:
                elem = next(elem_it)
            except StopIteration:
                break

            if elem.tag not in ("COMPARAM", "COMPLEX-COMPARAM"):
                continue

            subparam = create_any_comparam_from_et(elem, doc_frags)

            # the next element in the list *may* hold the physical
            # default value for the sub-parameter. if it is not the
            # correct tag, skip it! Note that the ODX specification
            # *only* allows to specify COMPLEX-PHYSICAL-DEFAULT-VALUE
            # tags here, even if the sub-parameter was a simple
            # parameter. This is probably a bug in the ODX
            # specification...
            tmp_it = elem_it
            try:
                elem = next(elem_it)
            except StopIteration:
                break

            if elem.tag != "COMPLEX-PHYSICAL-DEFAULT-VALUE":
                subparam.physical_default_value = create_complex_value_from_et(elem)
                elem_it = tmp_it
                continue

            subparams.append(subparam)

        allow_multiple_values_raw = odxstr_to_bool(et_element.get("ALLOW-MULTIPLE-VALUES"))

        return ComplexComparam(
            subparams=subparams,
            physical_default_value=[],
            allow_multiple_values_raw=allow_multiple_values_raw,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        for subparam in self.subparams:
            odxlinks.update(subparam._build_odxlinks())
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)
        for subparam in self.subparams:
            subparam._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)
        for subparam in self.subparams:
            subparam._resolve_snrefs(diag_layer)
