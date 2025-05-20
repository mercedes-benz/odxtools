# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from itertools import chain
from typing import Any
from xml.etree import ElementTree

from .diaglayers.basevariant import BaseVariant
from .diaglayers.ecuvariant import EcuVariant
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, resolve_snref
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ValidBaseVariant:
    ecu_variant_snrefs: list[str]
    base_variant_snref: str

    @property
    def ecu_variants(self) -> NamedItemList[EcuVariant]:
        return self._ecu_variants

    @property
    def base_variant(self) -> BaseVariant:
        return self._base_variant

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ValidBaseVariant":
        ecu_variant_snrefs = []
        for ecuv_snref_elem in et_element.iterfind("ECU-VARIANT-SNREFS/ECU-VARIANT-SNREF"):
            ecu_variant_snrefs.append(odxrequire(ecuv_snref_elem.attrib["SHORT-NAME"]))

        basev_snref_elem = odxrequire(et_element.find("BASE-VARIANT-SNREF"))
        base_variant_snref = odxrequire(basev_snref_elem.attrib["SHORT-NAME"])

        return ValidBaseVariant(
            ecu_variant_snrefs=ecu_variant_snrefs, base_variant_snref=base_variant_snref)

    def __post_init__(self) -> None:
        self._ecu_variants: NamedItemList[EcuVariant]
        self._base_variant: BaseVariant

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}
        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        db = odxrequire(context.database)

        ecu_variants = chain(*[dlc.ecu_variants for dlc in db.diag_layer_containers])
        base_variants = chain(*[dlc.base_variants for dlc in db.diag_layer_containers])

        self._ecu_variants = NamedItemList[EcuVariant]()
        for ev_snref in self.ecu_variant_snrefs:
            self._ecu_variants.append(resolve_snref(ev_snref, ecu_variants, EcuVariant))

        self._base_variant = resolve_snref(self.base_variant_snref, base_variants, BaseVariant)
