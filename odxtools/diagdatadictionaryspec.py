# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from itertools import chain
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .dataobjectproperty import DataObjectProperty
from .dopbase import DopBase
from .dtcdop import DtcDop
from .dynamicendmarkerfield import DynamicEndmarkerField
from .dynamiclengthfield import DynamicLengthField
from .endofpdufield import EndOfPduField
from .environmentdata import EnvironmentData
from .environmentdatadescription import EnvironmentDataDescription
from .multiplexer import Multiplexer
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .staticfield import StaticField
from .structure import Structure
from .table import Table
from .unitspec import UnitSpec


@dataclass(kw_only=True)
class DiagDataDictionarySpec:
    admin_data: AdminData | None = None
    dtc_dops: NamedItemList[DtcDop] = field(default_factory=NamedItemList)
    env_data_descs: NamedItemList[EnvironmentDataDescription] = field(default_factory=NamedItemList)
    data_object_props: NamedItemList[DataObjectProperty] = field(default_factory=NamedItemList)
    structures: NamedItemList[Structure] = field(default_factory=NamedItemList)
    static_fields: NamedItemList[StaticField] = field(default_factory=NamedItemList)
    dynamic_length_fields: NamedItemList[DynamicLengthField] = field(default_factory=NamedItemList)
    dynamic_endmarker_fields: NamedItemList[DynamicEndmarkerField] = field(
        default_factory=NamedItemList)
    end_of_pdu_fields: NamedItemList[EndOfPduField] = field(default_factory=NamedItemList)
    muxs: NamedItemList[Multiplexer] = field(default_factory=NamedItemList)
    env_datas: NamedItemList[EnvironmentData] = field(default_factory=NamedItemList)
    unit_spec: UnitSpec | None = None
    tables: NamedItemList[Table] = field(default_factory=NamedItemList)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "DiagDataDictionarySpec":
        admin_data = None
        if (admin_data_elem := et_element.find("ADMIN-DATA")) is not None:
            admin_data = AdminData.from_et(admin_data_elem, context)

        dtc_dops = NamedItemList([
            DtcDop.from_et(dtc_dop_elem, context)
            for dtc_dop_elem in et_element.iterfind("DTC-DOPS/DTC-DOP")
        ])

        env_data_descs = NamedItemList([
            EnvironmentDataDescription.from_et(env_data_desc_element, context)
            for env_data_desc_element in et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC")
        ])

        data_object_props = NamedItemList([
            DataObjectProperty.from_et(dop_element, context)
            for dop_element in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ])

        structures = NamedItemList([
            Structure.from_et(structure_element, context)
            for structure_element in et_element.iterfind("STRUCTURES/STRUCTURE")
        ])

        static_fields = NamedItemList([
            StaticField.from_et(dl_element, context)
            for dl_element in et_element.iterfind("STATIC-FIELDS/STATIC-FIELD")
        ])

        dynamic_length_fields = NamedItemList([
            DynamicLengthField.from_et(dl_element, context)
            for dl_element in et_element.iterfind("DYNAMIC-LENGTH-FIELDS/DYNAMIC-LENGTH-FIELD")
        ])

        dynamic_endmarker_fields = NamedItemList([
            DynamicEndmarkerField.from_et(dl_element, context) for dl_element in
            et_element.iterfind("DYNAMIC-ENDMARKER-FIELDS/DYNAMIC-ENDMARKER-FIELD")
        ])

        end_of_pdu_fields = NamedItemList([
            EndOfPduField.from_et(eofp_element, context)
            for eofp_element in et_element.iterfind("END-OF-PDU-FIELDS/END-OF-PDU-FIELD")
        ])

        muxs = NamedItemList([
            Multiplexer.from_et(mux_element, context)
            for mux_element in et_element.iterfind("MUXS/MUX")
        ])

        env_data_elements = chain(
            et_element.iterfind("ENV-DATAS/ENV-DATA"),
            # ODX 2.0.0 says ENV-DATA-DESC could contain a list of ENV-DATAS
            et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC/ENV-DATAS/ENV-DATA"),
        )
        env_datas = NamedItemList([
            EnvironmentData.from_et(env_data_element, context)
            for env_data_element in env_data_elements
        ])

        if (spec_elem := et_element.find("UNIT-SPEC")) is not None:
            unit_spec = UnitSpec.from_et(spec_elem, context)
        else:
            unit_spec = None

        tables = NamedItemList([
            Table.from_et(table_element, context)
            for table_element in et_element.iterfind("TABLES/TABLE")
        ])

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return DiagDataDictionarySpec(
            admin_data=admin_data,
            dtc_dops=dtc_dops,
            env_data_descs=env_data_descs,
            data_object_props=data_object_props,
            structures=structures,
            static_fields=static_fields,
            dynamic_length_fields=dynamic_length_fields,
            dynamic_endmarker_fields=dynamic_endmarker_fields,
            end_of_pdu_fields=end_of_pdu_fields,
            muxs=muxs,
            env_datas=env_datas,
            unit_spec=unit_spec,
            tables=tables,
            sdgs=sdgs,
        )

    def __post_init__(self) -> None:
        self._all_data_object_properties: NamedItemList[DopBase] = NamedItemList(
            chain(
                self.dtc_dops,
                self.env_data_descs,
                self.data_object_props,
                self.structures,
                self.static_fields,
                self.dynamic_length_fields,
                self.dynamic_endmarker_fields,
                self.end_of_pdu_fields,
                self.muxs,
                self.env_datas,
            ))

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        # note that DataDictionarySpec objects do not exhibit an ODXLINK id.
        odxlinks = {}

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())
        for dtc_dop in self.dtc_dops:
            odxlinks.update(dtc_dop._build_odxlinks())
        for env_data_desc in self.env_data_descs:
            odxlinks.update(env_data_desc._build_odxlinks())
        for data_object_prop in self.data_object_props:
            odxlinks.update(data_object_prop._build_odxlinks())
        for structure in self.structures:
            odxlinks.update(structure._build_odxlinks())
        for static_field in self.static_fields:
            odxlinks.update(static_field._build_odxlinks())
        for dynamic_length_field in self.dynamic_length_fields:
            odxlinks.update(dynamic_length_field._build_odxlinks())
        for dynamic_endmarker_field in self.dynamic_endmarker_fields:
            odxlinks.update(dynamic_endmarker_field._build_odxlinks())
        for end_of_pdu_field in self.end_of_pdu_fields:
            odxlinks.update(end_of_pdu_field._build_odxlinks())
        for mux in self.muxs:
            odxlinks.update(mux._build_odxlinks())
        for env_data in self.env_datas:
            odxlinks.update(env_data._build_odxlinks())
        if self.unit_spec is not None:
            odxlinks.update(self.unit_spec._build_odxlinks())
        for table in self.tables:
            odxlinks.update(table._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        for dtc_dop in self.dtc_dops:
            dtc_dop._resolve_odxlinks(odxlinks)
        for env_data_desc in self.env_data_descs:
            env_data_desc._resolve_odxlinks(odxlinks)
        for data_object_prop in self.data_object_props:
            data_object_prop._resolve_odxlinks(odxlinks)
        for structure in self.structures:
            structure._resolve_odxlinks(odxlinks)
        for static_field in self.static_fields:
            static_field._resolve_odxlinks(odxlinks)
        for dynamic_length_field in self.dynamic_length_fields:
            dynamic_length_field._resolve_odxlinks(odxlinks)
        for dynamic_endmarker_field in self.dynamic_endmarker_fields:
            dynamic_endmarker_field._resolve_odxlinks(odxlinks)
        for end_of_pdu_field in self.end_of_pdu_fields:
            end_of_pdu_field._resolve_odxlinks(odxlinks)
        for mux in self.muxs:
            mux._resolve_odxlinks(odxlinks)
        for env_data in self.env_datas:
            env_data._resolve_odxlinks(odxlinks)
        if self.unit_spec is not None:
            self.unit_spec._resolve_odxlinks(odxlinks)
        for table in self.tables:
            table._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)
        for dtc_dop in self.dtc_dops:
            dtc_dop._resolve_snrefs(context)
        for env_data_desc in self.env_data_descs:
            env_data_desc._resolve_snrefs(context)
        for data_object_prop in self.data_object_props:
            data_object_prop._resolve_snrefs(context)
        for structure in self.structures:
            structure._resolve_snrefs(context)
        for static_field in self.static_fields:
            static_field._resolve_snrefs(context)
        for dynamic_length_field in self.dynamic_length_fields:
            dynamic_length_field._resolve_snrefs(context)
        for dynamic_endmarker_field in self.dynamic_endmarker_fields:
            dynamic_endmarker_field._resolve_snrefs(context)
        for end_of_pdu_field in self.end_of_pdu_fields:
            end_of_pdu_field._resolve_snrefs(context)
        for mux in self.muxs:
            mux._resolve_snrefs(context)
        for env_data in self.env_datas:
            env_data._resolve_snrefs(context)
        if self.unit_spec is not None:
            self.unit_spec._resolve_snrefs(context)
        for table in self.tables:
            table._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

    @property
    def all_data_object_properties(self) -> NamedItemList[DopBase]:
        return self._all_data_object_properties
