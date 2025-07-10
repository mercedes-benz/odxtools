# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional
from xml.etree import ElementTree

from .diaglayers.basevariant import BaseVariant
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext

if TYPE_CHECKING:
    from .logicallink import LogicalLink


@dataclass(kw_only=True)
class GroupMember:
    base_variant_ref: OdxLinkRef
    funct_resolution_link_ref: OdxLinkRef | None = None
    phys_resolution_link_ref: OdxLinkRef | None = None

    @property
    def base_variant(self) -> BaseVariant:
        return self._base_variant

    @property
    def funct_resolution_link(self) -> Optional["LogicalLink"]:
        return self._funct_resolution_link

    @property
    def phys_resolution_link(self) -> Optional["LogicalLink"]:
        return self._phys_resolution_link

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "GroupMember":
        base_variant_ref = OdxLinkRef.from_et(
            odxrequire(et_element.find("BASE-VARIANT-REF")), context)
        funct_resolution_link_ref = OdxLinkRef.from_et(
            et_element.find("FUNCT-RESOLUTION-LINK-REF"), context)
        phys_resolution_link_ref = OdxLinkRef.from_et(
            et_element.find("PHYS-RESOLUTION-LINK-REF"), context)

        return GroupMember(
            base_variant_ref=base_variant_ref,
            funct_resolution_link_ref=funct_resolution_link_ref,
            phys_resolution_link_ref=phys_resolution_link_ref)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._base_variant = odxlinks.resolve(self.base_variant_ref, BaseVariant)

        self._funct_resolution_link = None
        if self.funct_resolution_link_ref is not None:
            if TYPE_CHECKING:
                self._funct_resolution_link = odxlinks.resolve(self.funct_resolution_link_ref,
                                                               LogicalLink)
            else:
                self._funct_resolution_link = odxlinks.resolve(self.funct_resolution_link_ref)

        self._phys_resolution_link = None
        if self.phys_resolution_link_ref is not None:
            if TYPE_CHECKING:
                self._phys_resolution_link = odxlinks.resolve(self.phys_resolution_link_ref,
                                                              LogicalLink)
            else:
                self._phys_resolution_link = odxlinks.resolve(self.phys_resolution_link_ref)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
