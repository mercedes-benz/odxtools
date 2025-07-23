# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .ecumem import EcuMem
from .ecumemconnector import EcuMemConnector
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class Flash(OdxCategory):
    ecu_mems: NamedItemList[EcuMem] = field(default_factory=NamedItemList)
    ecu_mem_connectors: NamedItemList[EcuMemConnector] = field(default_factory=NamedItemList)
    additional_audiences: NamedItemList[AdditionalAudience] = field(default_factory=NamedItemList)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Flash":

        base_obj = OdxCategory.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(base_obj)

        ecu_mems = NamedItemList(
            [EcuMem.from_et(el, context) for el in et_element.iterfind("ECU-MEMS/ECU-MEM")])
        ecu_mem_connectors = NamedItemList([
            EcuMemConnector.from_et(el, context)
            for el in et_element.iterfind("ECU-MEM-CONNECTORS/ECU-MEM-CONNECTOR")
        ])
        additional_audiences = NamedItemList([
            AdditionalAudience.from_et(el, context)
            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")
        ])

        return Flash(
            ecu_mems=ecu_mems,
            ecu_mem_connectors=ecu_mem_connectors,
            additional_audiences=additional_audiences,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for ecu_mem in self.ecu_mems:
            odxlinks.update(ecu_mem._build_odxlinks())

        for ecu_mem_connector in self.ecu_mem_connectors:
            odxlinks.update(ecu_mem_connector._build_odxlinks())

        for additional_audiences in self.additional_audiences:
            odxlinks.update(additional_audiences._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for ecu_mem in self.ecu_mems:
            ecu_mem._resolve_odxlinks(odxlinks)

        for ecu_mem_connector in self.ecu_mem_connectors:
            ecu_mem_connector._resolve_odxlinks(odxlinks)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for ecu_mem in self.ecu_mems:
            ecu_mem._resolve_snrefs(context)

        for ecu_mem_connector in self.ecu_mem_connectors:
            ecu_mem_connector._resolve_snrefs(context)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_snrefs(context)
