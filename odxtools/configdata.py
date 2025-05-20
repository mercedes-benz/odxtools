# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .configrecord import ConfigRecord
from .element import NamedElement
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict
from .validbasevariant import ValidBaseVariant


@dataclass(kw_only=True)
class ConfigData(NamedElement):
    """This class represents a CONFIG-DATA."""
    valid_base_variants: list[ValidBaseVariant]
    config_records: NamedItemList[ConfigRecord]
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ConfigData":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        valid_base_variants = [
            ValidBaseVariant.from_et(vbv_elem, context)
            for vbv_elem in et_element.iterfind("VALID-BASE-VARIANTS/VALID-BASE-VARIANT")
        ]
        config_records = NamedItemList([
            ConfigRecord.from_et(cr_elem, context)
            for cr_elem in et_element.iterfind("CONFIG-RECORDS/CONFIG-RECORD")
        ])
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return ConfigData(
            valid_base_variants=valid_base_variants,
            config_records=config_records,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for valid_base_variant in self.valid_base_variants:
            result.update(valid_base_variant._build_odxlinks())
        for config_record in self.config_records:
            result.update(config_record._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for valid_base_variant in self.valid_base_variants:
            valid_base_variant._resolve_odxlinks(odxlinks)
        for config_record in self.config_records:
            config_record._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for valid_base_variant in self.valid_base_variants:
            valid_base_variant._resolve_snrefs(context)
        for config_record in self.config_records:
            config_record._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
