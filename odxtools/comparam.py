# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .dataobjectproperty import DataObjectProperty
from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Comparam(BaseComparam):
    dop_ref: OdxLinkRef
    physical_default_value: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Comparam":
        # create an "empty" Comparam object without calling the
        # "official" constructor. We need to do this because we need
        # all data attributes of the class to call the constructor,
        # including those which are supposed to be handled by the base
        # class (i.e., ComparamBase)
        result = Comparam.__new__(Comparam)

        # initialize the new "empty" object from the ElementTree
        result.__init_from_et__(et_element, doc_frags)

        return result

    def __init_from_et__(self, et_element: ElementTree.Element,
                         doc_frags: List[OdxDocFragment]) -> None:
        super().__init_from_et__(et_element, doc_frags)

        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags))

        self.dop_ref = dop_ref
        self.physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

    @property
    def dop(self) -> DataObjectProperty:
        """The data object property describing this parameter."""
        return self._dop

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Resolves the reference to the dop"""
        super()._resolve_odxlinks(odxlinks)

        self._dop = odxlinks.resolve(self.dop_ref)
        if not isinstance(self._dop, DataObjectProperty):
            odxraise()

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)
