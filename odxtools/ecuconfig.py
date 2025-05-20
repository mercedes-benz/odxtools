# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .configdata import ConfigData
from .configdatadictionaryspec import ConfigDataDictionarySpec
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class EcuConfig(OdxCategory):
    config_datas: NamedItemList[ConfigData]
    additional_audiences: NamedItemList[AdditionalAudience]
    config_data_dictionary_spec: ConfigDataDictionarySpec | None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuConfig":

        base_obj = OdxCategory.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(base_obj)

        config_datas = NamedItemList([
            ConfigData.from_et(el, context)
            for el in et_element.iterfind("CONFIG-DATAS/CONFIG-DATA")
        ])
        additional_audiences = NamedItemList([
            AdditionalAudience.from_et(el, context)
            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")
        ])
        config_data_dictionary_spec = None
        if (cdd_elem := et_element.find("CONFIG-DATA-DICTIONARY-SPEC")) is not None:
            config_data_dictionary_spec = ConfigDataDictionarySpec.from_et(cdd_elem, context)

        return EcuConfig(
            config_datas=config_datas,
            additional_audiences=additional_audiences,
            config_data_dictionary_spec=config_data_dictionary_spec,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for config_data in self.config_datas:
            odxlinks.update(config_data._build_odxlinks())

        for additional_audience in self.additional_audiences:
            odxlinks.update(additional_audience._build_odxlinks())

        if self.config_data_dictionary_spec is not None:
            odxlinks.update(self.config_data_dictionary_spec._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for config_data in self.config_datas:
            config_data._resolve_odxlinks(odxlinks)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_odxlinks(odxlinks)

        if self.config_data_dictionary_spec is not None:
            self.config_data_dictionary_spec._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for config_data in self.config_datas:
            config_data._resolve_snrefs(context)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_snrefs(context)

        if self.config_data_dictionary_spec is not None:
            self.config_data_dictionary_spec._resolve_snrefs(context)
