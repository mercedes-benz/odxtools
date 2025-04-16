# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagnostictroublecode import DiagnosticTroubleCode
from .dtcdop import DtcDop
from .element import NamedElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DtcConnector(NamedElement):
    dtc_dop_ref: OdxLinkRef
    dtc_snref: str

    @property
    def dtc_dop(self) -> DtcDop:
        return self._dtc_dop

    @property
    def dtc(self) -> DiagnosticTroubleCode:
        return self._dtc

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DtcConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        dtc_dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DTC-DOP-REF"), context))
        dtc_snref_el = odxrequire(et_element.find("DTC-SNREF"))
        dtc_snref = odxrequire(dtc_snref_el.get("SHORT-NAME"))

        return DtcConnector(dtc_dop_ref=dtc_dop_ref, dtc_snref=dtc_snref, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dtc_dop = odxlinks.resolve(self.dtc_dop_ref, DtcDop)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._dtc = resolve_snref(self.dtc_snref, self._dtc_dop.dtcs, DiagnosticTroubleCode)
