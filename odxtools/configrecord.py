# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .audience import Audience
from .configiditem import ConfigIdItem
from .dataiditem import DataIdItem
from .datarecord import DataRecord
from .diagcommdataconnector import DiagCommDataConnector
from .element import NamedElement
from .exceptions import odxrequire
from .identvalue import IdentValue
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .optionitem import OptionItem
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .systemitem import SystemItem
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ConfigRecord(NamedElement):
    """This class represents a CONFIG-RECORD."""
    config_id_item: ConfigIdItem | None = None
    diag_comm_data_connectors: list[DiagCommDataConnector] = field(default_factory=list)
    config_id: IdentValue | None = None
    data_records: NamedItemList[DataRecord] = field(default_factory=NamedItemList)
    audience: Audience | None = None
    system_items: NamedItemList[SystemItem] = field(default_factory=NamedItemList)
    data_id_item: DataIdItem | None = None
    option_items: NamedItemList[OptionItem] = field(default_factory=NamedItemList)
    default_data_record_snref: str | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ConfigRecord":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        config_id_item = None
        if (cid_elem := et_element.find("CONFIG-ID-ITEM")) is not None:
            config_id_item = ConfigIdItem.from_et(cid_elem, context)
        diag_comm_data_connectors = [
            DiagCommDataConnector.from_et(dcdc_elem, context) for dcdc_elem in et_element.iterfind(
                "DIAG-COMM-DATA-CONNECTORS/DIAG-COMM-DATA-CONNECTOR")
        ]
        config_id = None
        if (cid_elem := et_element.find("CONFIG-ID")) is not None:
            config_id = IdentValue.from_et(cid_elem, context)
        data_records = NamedItemList([
            DataRecord.from_et(dr_elem, context)
            for dr_elem in et_element.iterfind("DATA-RECORDS/DATA-RECORD")
        ])
        audience = None
        if (aud_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(aud_elem, context)
        system_items = NamedItemList([
            SystemItem.from_et(si_elem, context)
            for si_elem in et_element.iterfind("SYSTEM-ITEMS/SYSTEM-ITEM")
        ])
        data_id_item = None
        if (dii_elem := et_element.find("DATA-ID-ITEM")) is not None:
            data_id_item = DataIdItem.from_et(dii_elem, context)
        option_items = NamedItemList([
            OptionItem.from_et(si_elem, context)
            for si_elem in et_element.iterfind("OPTION-ITEMS/OPTION-ITEM")
        ])
        default_data_record_snref = None
        if (default_data_record_snref_elem :=
                et_element.find("DEFAULT-DATA-RECORD-SNREF")) is not None:
            default_data_record_snref = odxrequire(
                default_data_record_snref_elem.attrib.get("SHORT-NAME"))
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return ConfigRecord(
            config_id_item=config_id_item,
            diag_comm_data_connectors=diag_comm_data_connectors,
            config_id=config_id,
            data_records=data_records,
            audience=audience,
            system_items=system_items,
            data_id_item=data_id_item,
            option_items=option_items,
            default_data_record_snref=default_data_record_snref,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.config_id_item is not None:
            result.update(self.config_id_item._build_odxlinks())
        for diag_comm_data_connector in self.diag_comm_data_connectors:
            result.update(diag_comm_data_connector._build_odxlinks())
        for data_record in self.data_records:
            result.update(data_record._build_odxlinks())
        if self.audience is not None:
            result.update(self.audience._build_odxlinks())
        for system_item in self.system_items:
            result.update(system_item._build_odxlinks())
        if self.data_id_item is not None:
            result.update(self.data_id_item._build_odxlinks())
        for option_item in self.option_items:
            result.update(option_item._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.config_id_item is not None:
            self.config_id_item._resolve_odxlinks(odxlinks)
        for diag_comm_data_connector in self.diag_comm_data_connectors:
            diag_comm_data_connector._resolve_odxlinks(odxlinks)
        for data_record in self.data_records:
            data_record._resolve_odxlinks(odxlinks)
        if self.audience is not None:
            self.audience._resolve_odxlinks(odxlinks)
        for system_item in self.system_items:
            system_item._resolve_odxlinks(odxlinks)
        if self.data_id_item is not None:
            self.data_id_item._resolve_odxlinks(odxlinks)
        for option_item in self.option_items:
            option_item._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.config_id_item is not None:
            self.config_id_item._resolve_snrefs(context)
        for diag_comm_data_connector in self.diag_comm_data_connectors:
            diag_comm_data_connector._resolve_snrefs(context)
        for data_record in self.data_records:
            data_record._resolve_snrefs(context)
        if self.audience is not None:
            self.audience._resolve_snrefs(context)
        for system_item in self.system_items:
            system_item._resolve_snrefs(context)
        if self.data_id_item is not None:
            self.data_id_item._resolve_snrefs(context)
        for option_item in self.option_items:
            option_item._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
