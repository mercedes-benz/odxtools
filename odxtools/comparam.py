# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .dataobjectproperty import DataObjectProperty
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import AtomicOdxType
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Comparam(BaseComparam):
    physical_default_value_raw: str
    dop_ref: OdxLinkRef

    @property
    def physical_default_value(self) -> AtomicOdxType:
        return self._physical_default_value

    @property
    def dop(self) -> DataObjectProperty:
        """The data object property applicable to this parameter."""
        return self._dop

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Comparam":
        kwargs = dataclass_fields_asdict(BaseComparam.from_et(et_element, context))

        physical_default_value_raw = odxrequire(et_element.findtext("PHYSICAL-DEFAULT-VALUE"))
        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), context))

        return Comparam(
            dop_ref=dop_ref, physical_default_value_raw=physical_default_value_raw, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Resolves the reference to the dop"""
        super()._resolve_odxlinks(odxlinks)

        self._dop = odxlinks.resolve(self.dop_ref, DataObjectProperty)
        self._physical_default_value = self._dop.physical_type.base_data_type.from_string(
            self.physical_default_value_raw)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
