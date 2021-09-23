# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

from odxtools.utils import read_description_from_odx
from odxtools.exceptions import DecodeError
from odxtools.structures import BasicStructure
from .globals import logger
from .dataobjectproperty import DopBase


class EndOfPduField(DopBase):
    """ End of PDU fields are structures that are repeated until the end of the PDU """

    def __init__(self,
                 id,
                 short_name,
                 structure=None,
                 structure_ref=None,
                 structure_snref=None,
                 min_number_of_items=0,
                 max_number_of_items=None,
                 is_visible=False,
                 long_name=None,
                 description=None):
        super().__init__(id, short_name, long_name=long_name,
                         description=description, is_visible=is_visible)

        self.structure_snref = structure_snref
        self.structure_ref = structure_ref

        self._structure = structure
        if structure:
            self.structure_ref = structure.id
        assert self.structure_ref or self.structure_snref

        self.min_number_of_items = min_number_of_items
        self.max_number_of_items = max_number_of_items

        self.is_visible = is_visible

    @property
    def structure(self) -> BasicStructure:
        """may be a Structure or a env-data-desc"""
        return self._structure

    @property
    def bit_length(self):
        return self.structure.bit_length

    def convert_physical_to_internal(self, physical_value):
        return self.structure.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value, bit_position: int):
        return self.structure.convert_physical_to_bytes(physical_value, bit_position)

    def convert_bytes_to_physical(self, byte_code: int, byte_position=0, bit_position=0):
        next_byte_position = byte_position
        value = []
        while len(byte_code) > next_byte_position:
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            new_value, next_byte_position = self.structure.convert_bytes_to_physical(byte_code,
                                                                                     byte_position=next_byte_position,
                                                                                     bit_position=bit_position)

            value.append(new_value)
        return value, next_byte_position

    def _resolve_references(self, parent_dl, id_lookup):
        """Recursively resolve any references (odxlinks or sn-refs)
        """
        if self.structure_ref is not None:
            self._structure = id_lookup[self.structure_ref]
        else:
            self._structure = parent_dl.data_object_properties[self.structure_snref]

    def __repr__(self) -> str:
        return \
            f"EndOfPduField(short_name='{self.short_name}', " + \
                          f"ref='{self.structure.id}')"

    def __str__(self):
        return "\n".join([
            f"EndOfPduField(short_name='{self.short_name}', ref='{self.structure.id}')"
        ] + [
            " " + str(self.structure).replace("\n", "\n ")
        ])


def read_end_of_pdu_field_from_odx(et_element):
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    description = read_description_from_odx(et_element.find("DESC"))

    if et_element.find("BASIC-STRUCTURE-REF") is not None:
        structure_ref = et_element.find(
            "BASIC-STRUCTURE-REF").get("ID-REF")
        structure_snref = None

    if et_element.find("BASIC-STRUCTURE-SNREF") is not None:
        structure_ref = None
        structure_snref = et_element.find(
            "BASIC-STRUCTURE-SNREF").get("SHORT-NAME")

    if et_element.find("ENV-DATA-DESC-REF") is not None:
        structure_ref = et_element.get("ENV-DATA-DESC-REF")
        structure_snref = None

    if et_element.find("ENV-DATA-DESC-SNREF") is not None:
        structure_ref = None
        structure_snref = et_element.get("ENV-DATA-DESC-SNREF")

    if et_element.find("MIN-NUMBER-OF-ITEMS") is not None:
        min_number_of_items = int(
            et_element.find("MIN-NUMBER-OF-ITEMS").text)
    else:
        min_number_of_items = None
    if et_element.find("MAX-NUMBER-OF-ITEMS") is not None:
        max_number_of_items = int(
            et_element.find("MAX-NUMBER-OF-ITEMS").text)
    else:
        max_number_of_items = None

    is_visible = et_element.get("IS-VISIBLE")
    if is_visible is not None:
        assert is_visible in ["true", "false"]
        is_visible = is_visible == "true"
    else:
        is_visible = False
    eopf = EndOfPduField(id,
                         short_name,
                         long_name=long_name,
                         description=description,
                         structure_ref=structure_ref,
                         structure_snref=structure_snref,
                         min_number_of_items=min_number_of_items,
                         max_number_of_items=max_number_of_items,
                         is_visible=is_visible)

    return eopf
