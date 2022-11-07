# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Optional, Any, Dict, List

from .utils import short_name_as_id
from .dataobjectproperty import (
    DataObjectProperty,
    DtcDop,
    read_data_object_property_from_odx,
)
from .endofpdufield import EndOfPduField, read_end_of_pdu_field_from_odx
from .envdata import read_env_data_from_odx, EnvironmentData
from .envdatadesc import read_env_data_desc_from_odx, EnvironmentDataDescription
from .globals import logger
from .multiplexer import Multiplexer, read_mux_from_odx
from .nameditemlist import NamedItemList
from .structures import BasicStructure, read_structure_from_odx
from .table import read_table_from_odx, Table
from .units import read_unit_spec_from_odx, UnitSpec
from .odxlink import OdxLinkId, OdxLinkDatabase, OdxDocFragment

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

def _construct_named_item_list(iterable):
    return NamedItemList(short_name_as_id, iterable)


@dataclass()
class DiagDataDictionarySpec:
    dtc_dops: NamedItemList[DtcDop] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    data_object_props: NamedItemList[DataObjectProperty] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    structures: NamedItemList[BasicStructure] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    end_of_pdu_fields: NamedItemList[EndOfPduField] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    tables: NamedItemList[Table] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    env_data_descs: NamedItemList[EnvironmentDataDescription] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    env_datas: NamedItemList[EnvironmentData] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    muxs: NamedItemList[Multiplexer] = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    unit_spec: Optional[UnitSpec] = None

    def __post_init__(self):
        self._all_data_object_properties = _construct_named_item_list(
            chain(
                self.data_object_props,
                self.structures,
                self.end_of_pdu_fields,
                self.dtc_dops,
                self.tables,
            )
        )

        # The attributes are already initialized as (most likely normal) lists.
        # Convert them to NamedItemLists if necessary
        if not isinstance(self.dtc_dops, NamedItemList):
            self.dtc_dops = _construct_named_item_list(self.dtc_dops)

        if not isinstance(self.data_object_props, NamedItemList):
            self.data_object_props = _construct_named_item_list(self.data_object_props)

        if not isinstance(self.structures, NamedItemList):
            self.structures = _construct_named_item_list(self.structures)

        if not isinstance(self.end_of_pdu_fields, NamedItemList):
            self.end_of_pdu_fields = _construct_named_item_list(self.end_of_pdu_fields)

        if not isinstance(self.tables, NamedItemList):
            self.tables = _construct_named_item_list(self.tables)

        if not isinstance(self.env_data_descs, NamedItemList):
            self.env_data_descs = _construct_named_item_list(self.env_data_descs)

        if not isinstance(self.env_datas, NamedItemList):
            self.env_datas = _construct_named_item_list(self.env_datas)

        if not isinstance(self.muxs, NamedItemList):
            self.muxs = _construct_named_item_list(self.muxs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {}
        for obj in chain(
            self.data_object_props, self.structures, self.end_of_pdu_fields, self.tables
        ):
            odxlinks[obj.odx_id] = obj

        for table in self.tables:
            odxlinks.update(table._build_odxlinks())

        for env_data_desc in self.env_data_descs:
            odxlinks.update(env_data_desc._build_odxlinks())

        for env_data in self.env_datas:
            odxlinks.update(env_data._build_odxlinks())

        for mux in self.muxs:
            odxlinks.update(mux._build_odxlinks())

        for obj in self.dtc_dops:
            odxlinks.update(obj._build_odxlinks())

        if self.unit_spec:
            odxlinks.update(self.unit_spec._build_odxlinks())

        return odxlinks

    def _resolve_references(self,
                            parent_dl: "DiagLayer",
                            odxlinks: OdxLinkDatabase):
        for dop in chain(
            self.dtc_dops,
            self.data_object_props,
            self.tables,
        ):
            dop._resolve_references(odxlinks)

        for struct in chain(self.structures, self.end_of_pdu_fields):
            struct._resolve_references(parent_dl, odxlinks)

        for env_data in chain(
            self.env_datas,
        ):
            env_data._resolve_references(parent_dl, odxlinks)

        for mux in chain(
            self.muxs,
        ):
            mux._resolve_references(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_references(odxlinks)

    @property
    def all_data_object_properties(self):
        return self._all_data_object_properties


def read_diag_data_dictionary_spec_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    # Parse DOP-BASEs
    data_object_props = [
        read_data_object_property_from_odx(dop_element, doc_frags)
        for dop_element in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
    ]

    structures = []
    for structure_element in et_element.iterfind("STRUCTURES/STRUCTURE"):
        structure = read_structure_from_odx(structure_element, doc_frags)
        assert structure is not None
        structures.append(structure)

    end_of_pdu_fields = [
        read_end_of_pdu_field_from_odx(eofp_element, doc_frags)
        for eofp_element in et_element.iterfind("END-OF-PDU-FIELDS/END-OF-PDU-FIELD")
    ]

    dtc_dops = []
    for dop_element in et_element.iterfind("DTC-DOPS/DTC-DOP"):
        dop = read_data_object_property_from_odx(dop_element, doc_frags)
        assert isinstance(dop, DtcDop)
        dtc_dops.append(dop)

    tables = [
        read_table_from_odx(table_element, doc_frags)
        for table_element in et_element.iterfind("TABLES/TABLE")
    ]

    env_data_descs = [
        read_env_data_desc_from_odx(env_data_desc_element, doc_frags)
        for env_data_desc_element in et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC")
    ]

    env_data_elements = chain(
        et_element.iterfind("ENV-DATAS/ENV-DATA"),
        # ODX 2.0.0 says ENV-DATA-DESC could contain a list of ENV-DATAS
        et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC/ENV-DATAS/ENV-DATA"),
    )
    env_datas = [
        read_env_data_from_odx(env_data_element, doc_frags)
        for env_data_element in env_data_elements
    ]

    muxs = [
        read_mux_from_odx(mux_element, doc_frags)
        for mux_element in et_element.iterfind("MUXS/MUX")
    ]

    if et_element.find("UNIT-SPEC") is not None:
        unit_spec = read_unit_spec_from_odx(et_element.find("UNIT-SPEC"), doc_frags)
    else:
        unit_spec = None

    # TODO: Parse different specs.. Which of them are needed?
    for (path, name) in [
        ("STATIC-FIELDS", "static fields"),
        ("DYNAMIC-LENGTH-FIELDS/DYNAMIC-LENGTH-FIELD", "dynamic length fields"),
        (
            "DYNAMIC-ENDMARKER-FIELDS/DYNAMIC-ENDMARKER-FIELD",
            "dynamic endmarker fields",
        ),
    ]:
        num = len(list(et_element.iterfind(path)))
        if num > 0:
            logger.info(f"Not implemented: Did not parse {num} {name}.")

    return DiagDataDictionarySpec(
        data_object_props=NamedItemList(short_name_as_id, data_object_props),
        structures=NamedItemList(short_name_as_id, structures),
        end_of_pdu_fields=NamedItemList(short_name_as_id, end_of_pdu_fields),
        dtc_dops=NamedItemList(short_name_as_id, dtc_dops),
        unit_spec=unit_spec,
        tables=NamedItemList(short_name_as_id, tables),
        env_data_descs=NamedItemList(short_name_as_id, env_data_descs),
        env_datas=NamedItemList(short_name_as_id, env_datas),
        muxs=NamedItemList(short_name_as_id, muxs),
    )
