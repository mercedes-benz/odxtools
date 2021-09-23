# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

from dataclasses import dataclass, field
from itertools import chain

from .nameditemlist import NamedItemList
from .dataobjectproperty import read_data_object_property_from_odx
from .endofpdufield import read_end_of_pdu_field_from_odx
from .structures import read_structure_from_odx
from .globals import logger


def _construct_named_item_list(iterable):
    return NamedItemList(lambda x: x.short_name, iterable)


@dataclass()
class DiagDataDictionarySpec:
    dtc_dops: NamedItemList = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    data_object_props: NamedItemList = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    structures: NamedItemList = field(
        default_factory=lambda: _construct_named_item_list([])
    )
    end_of_pdu_fields: NamedItemList = field(
        default_factory=lambda: _construct_named_item_list([])
    )

    def __post_init__(self):
        self._all_data_object_properties = _construct_named_item_list(
            chain(self.data_object_props, self.structures,
                  self.end_of_pdu_fields, self.dtc_dops)
        )

        # The attributes are already initialized as (most likely normal) lists.
        # Convert them to NamedItemLists if necessary
        if not isinstance(self.dtc_dops, NamedItemList):
            self.dtc_dops = _construct_named_item_list(
                self.dtc_dops)

        if not isinstance(self.data_object_props, NamedItemList):
            self.data_object_props = _construct_named_item_list(
                self.data_object_props)

        if not isinstance(self.structures, NamedItemList):
            self.structures = _construct_named_item_list(
                self.structures)

        if not isinstance(self.end_of_pdu_fields, NamedItemList):
            self.end_of_pdu_fields = _construct_named_item_list(
                self.end_of_pdu_fields)

    @property
    def all_data_object_properties(self):
        return self._all_data_object_properties


def read_diag_data_dictionary_spec_from_odx(et_element):
    # Parse DOP-BASEs
    data_object_props = [read_data_object_property_from_odx(dop_element)
                         for dop_element in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")]

    structures = [read_structure_from_odx(structure_element)
                  for structure_element in et_element.iterfind("STRUCTURES/STRUCTURE")]

    end_of_pdu_fields = [read_end_of_pdu_field_from_odx(eopf_element)
                         for eopf_element in et_element.iterfind("END-OF-PDU-FIELDS/END-OF-PDU-FIELD")]

    dtc_dops = [read_data_object_property_from_odx(dop_element)
                for dop_element in et_element.iterfind("DTC-DOPS/DTC-DOP")]

    # TODO: Parse different specs.. Which of them are needed?
    for (path, name) in [
        ('ENV-DATA-DESCS/ENV-DATA-DESC', 'ENV-DATA-DESCs'),
        ('STATIC-FIELDS', 'static fields'),
        ('DYNAMIC-LENGTH-FIELDS/DYNAMIC-LENGTH-FIELD', 'dynamic length fields'),
        ('DYNAMIC-ENDMARKER-FIELDS/DYNAMIC-ENDMARKER-FIELD',
         'dynamic endmarker fields'),
        ('MUXS/MUX', 'MUXs'),
        ('ENV-DATAS/ENV-DATA', 'ENV-DATAs'),
        ('TABLES/TABLE', 'tables'),
    ]:
        num = len(list(et_element.iterfind(path)))
        if num > 0:
            logger.info(f"Not implemented: Did not parse {num} {name}.")

    return DiagDataDictionarySpec(
        data_object_props=data_object_props,
        structures=structures,
        end_of_pdu_fields=end_of_pdu_fields,
        dtc_dops=dtc_dops
    )
