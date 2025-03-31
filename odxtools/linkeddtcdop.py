# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from .diagnostictroublecode import DiagnosticTroubleCode
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext

if TYPE_CHECKING:
    from .dtcdop import DtcDop


@dataclass
class LinkedDtcDop:
    not_inherited_dtc_snrefs: List[str]
    dtc_dop_ref: OdxLinkRef

    @property
    def not_inherited_dtcs(self) -> NamedItemList[DiagnosticTroubleCode]:
        return self._not_inherited_dtcs

    @property
    def dtc_dop(self) -> "DtcDop":
        return self._dtc_dop

    @property
    def short_name(self) -> str:
        return self._dtc_dop.short_name

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "LinkedDtcDop":
        not_inherited_dtc_snrefs = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("NOT-INHERITED-DTC-SNREFS/"
                                          "NOT-INHERITED-DTC-SNREF")
        ]

        dtc_dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DTC-DOP-REF"), doc_frags))

        return LinkedDtcDop(
            not_inherited_dtc_snrefs=not_inherited_dtc_snrefs, dtc_dop_ref=dtc_dop_ref)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if TYPE_CHECKING:
            self._dtc_dop = odxlinks.resolve(self.dtc_dop_ref, DtcDop)
        else:
            self._dtc_dop = odxlinks.resolve(self.dtc_dop_ref)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        dtc_dop = self._dtc_dop
        not_inherited_dtcs = [
            resolve_snref(ni_snref, dtc_dop.dtcs, DiagnosticTroubleCode)
            for ni_snref in self.not_inherited_dtc_snrefs
        ]

        self._not_inherited_dtcs = NamedItemList(not_inherited_dtcs)
