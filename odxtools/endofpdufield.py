# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import TYPE_CHECKING, List, Union

from .utils import read_description_from_odx
from .odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment, OdxLinkDatabase
from .structures import BasicStructure
from .dataobjectproperty import DopBase
from .decodestate import DecodeState
from .encodestate import EncodeState

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class EndOfPduField(DopBase):
    """ End of PDU fields are structures that are repeated until the end of the PDU """

    def __init__(self,
                 odx_id,
                 short_name,
                 structure=None,
                 structure_ref=None,
                 structure_snref=None,
                 min_number_of_items=0,
                 max_number_of_items=None,
                 is_visible=False,
                 long_name=None,
                 description=None):
        super().__init__(odx_id, short_name, long_name=long_name,
                         description=description, is_visible=is_visible)

        self.structure_snref = structure_snref
        self.structure_ref = structure_ref

        self._structure = structure
        if structure:
            self.structure_ref = OdxLinkRef.from_id(structure.odx_id)
        assert self.structure_ref or self.structure_snref

        self.min_number_of_items = min_number_of_items
        self.max_number_of_items = max_number_of_items

        self.is_visible = is_visible

    @property
    def structure(self) -> "BasicStructure":
        """may be a Structure or a env-data-desc"""
        return self._structure

    @property
    def bit_length(self):
        return self.structure.bit_length

    def convert_physical_to_internal(self, physical_value):
        return self.structure.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value: Union[dict, List[dict]], encode_state: EncodeState, bit_position: int = 0):
        assert bit_position == 0, "End of PDU field must be byte aligned. Is there an error in reading the .odx?"
        if isinstance(physical_value, dict):
            # If the value is given as a dict, the End of PDU field behaves like the underlying structure.
            return self.structure.convert_physical_to_bytes(physical_value, encode_state)
        else:
            assert isinstance(physical_value, List), "The value of an End of PDU field must be a list or a dict." 
            # If the value is given as a list, each list element is a encoded seperately using the structure.
            coded_rpc = bytes()
            for value in physical_value:
                encode_state = encode_state._replace(coded_message=bytes())
                coded_rpc += self.structure.convert_physical_to_bytes(value, encode_state)
            return coded_rpc

    def convert_bytes_to_physical(self, decode_state: DecodeState, bit_position: int = 0):
        next_byte_position = decode_state.next_byte_position
        byte_code = decode_state.coded_message

        value = []
        while len(byte_code) > next_byte_position:
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            new_value, next_byte_position = self.structure.convert_bytes_to_physical(decode_state,
                                                                                     bit_position=bit_position)
            # Update next byte_position
            decode_state = decode_state._replace(next_byte_position=next_byte_position)
            value.append(new_value)

        return value, next_byte_position

    def _resolve_references(self,
                            parent_dl: "DiagLayer",
                            odxlinks: OdxLinkDatabase) \
     -> None:
        """Recursively resolve any references (odxlinks or sn-refs)
        """
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)
        else:
            self._structure = parent_dl.data_object_properties[self.structure_snref]

    def __repr__(self) -> str:
        return f"EndOfPduField(short_name='{self.short_name}', ref='{self.structure.odx_id}')"

    def __str__(self):
        return "\n".join([
            f"EndOfPduField(short_name='{self.short_name}', ref='{self.structure.odx_id}')"
        ] + [
            " " + str(self.structure).replace("\n", "\n ")
        ])


def read_end_of_pdu_field_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> EndOfPduField:
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    structure_ref = OdxLinkRef.from_et(et_element.find("BASIC-STRUCTURE-REF"), doc_frags)

    structure_snref = None
    if et_element.find("BASIC-STRUCTURE-SNREF") is not None:
        structure_snref = et_element.find(
            "BASIC-STRUCTURE-SNREF").get("SHORT-NAME")
    assert (structure_ref is not None) or (structure_snref is not None)

    if et_element.find("ENV-DATA-DESC-REF") is not None:
        structure_ref = OdxLinkRef.from_et(et_element.get("ENV-DATA-DESC-REF"), doc_frags)
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
    eopf = EndOfPduField(odx_id,
                         short_name,
                         long_name=long_name,
                         description=description,
                         structure_ref=structure_ref,
                         structure_snref=structure_snref,
                         min_number_of_items=min_number_of_items,
                         max_number_of_items=max_number_of_items,
                         is_visible=is_visible)

    return eopf
