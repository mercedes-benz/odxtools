# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from copy import copy
from typing import TYPE_CHECKING, List, Optional, Union

from .dataobjectproperty import DopBase
from .decodestate import DecodeState
from .encodestate import EncodeState
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValueDict, odxstr_to_bool
from .specialdata import create_sdgs_from_et
from .structures import BasicStructure
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class EndOfPduField(DopBase):
    """End of PDU fields are structures that are repeated until the end of the PDU"""

    def __init__(
        self,
        *,
        structure_ref: Optional[OdxLinkRef],
        structure_snref: Optional[str],
        env_data_desc_ref: Optional[OdxLinkRef],
        env_data_desc_snref: Optional[str],
        min_number_of_items: Optional[int],
        max_number_of_items: Optional[int],
        **kwargs,
    ):
        super().__init__(**kwargs)

        num_struct_refs = 0 if structure_ref is None else 1
        num_struct_refs += 0 if structure_snref is None else 1

        num_edd_refs = 0 if env_data_desc_ref is None else 1
        num_edd_refs += 0 if env_data_desc_snref is None else 1
        assert num_struct_refs + num_edd_refs == 1, (
            "END-OF-PDU-FIELDs need to specify exactly one reference to a "
            "structure of an environment data description")

        self.structure_snref = structure_snref
        self.structure_ref = structure_ref
        self.env_data_desc_snref = env_data_desc_snref
        self.env_data_desc_ref = env_data_desc_ref

        self.min_number_of_items = min_number_of_items
        self.max_number_of_items = max_number_of_items

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "EndOfPduField":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        structure_ref = OdxLinkRef.from_et(et_element.find("BASIC-STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (edsnr_elem := et_element.find("BASIC-STRUCTURE-SNREF")) is not None:
            structure_snref = edsnr_elem.get("SHORT-NAME")

        env_data_desc_ref = OdxLinkRef.from_et(et_element.find("ENV-DATA-DESC-REF"), doc_frags)
        env_data_desc_snref = None
        if (edsnr_elem := et_element.find("ENV-DATA-DESC-SNREF")) is not None:
            env_data_desc_snref = edsnr_elem.get("SHORT-NAME")

        if et_element.find("MIN-NUMBER-OF-ITEMS") is not None:
            min_number_of_items = int(et_element.findtext("MIN-NUMBER-OF-ITEMS"))
        else:
            min_number_of_items = None
        if et_element.find("MAX-NUMBER-OF-ITEMS") is not None:
            max_number_of_items = int(et_element.findtext("MAX-NUMBER-OF-ITEMS"))
        else:
            max_number_of_items = None

        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        eopf = EndOfPduField(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            sdgs=sdgs,
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            env_data_desc_ref=env_data_desc_ref,
            env_data_desc_snref=env_data_desc_snref,
            min_number_of_items=min_number_of_items,
            max_number_of_items=max_number_of_items,
            is_visible_raw=is_visible_raw,
        )

        return eopf

    @property
    def structure(self) -> "BasicStructure":
        """may be a Structure or a env-data-desc"""
        return self._structure

    @property
    def bit_length(self):
        return self.structure.bit_length

    def convert_physical_to_internal(self, physical_value):
        return self.structure.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(
        self,
        physical_value: ParameterValueDict,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:
        assert (bit_position == 0
               ), "End of PDU field must be byte aligned. Is there an error in reading the .odx?"
        if isinstance(physical_value, dict):
            # If the value is given as a dict, the End of PDU field behaves like the underlying structure.
            return self.structure.convert_physical_to_bytes(physical_value, encode_state)
        else:
            assert isinstance(physical_value,
                              list), "The value of an End-of-PDU-field must be a list or a dict."
            # If the value is given as a list, each list element is a encoded seperately using the structure.
            coded_rpc = bytes()
            for value in physical_value:
                coded_rpc += self.structure.convert_physical_to_bytes(value, encode_state)
            return coded_rpc

    def convert_bytes_to_physical(self, decode_state: DecodeState, bit_position: int = 0):
        decode_state = copy(decode_state)
        next_byte_position = decode_state.next_byte_position
        byte_code = decode_state.coded_message

        value = []
        while len(byte_code) > next_byte_position:
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            new_value, next_byte_position = self.structure.convert_bytes_to_physical(
                decode_state, bit_position=bit_position)
            # Update next byte_position
            decode_state.next_byte_position = next_byte_position
            value.append(new_value)

        return value, next_byte_position

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any odxlinks references"""
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)

        if self.env_data_desc_ref is not None:
            self._env_data_desc = odxlinks.resolve(self.env_data_desc_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        """Recursively resolve any short-name references"""
        if self.structure_snref is not None:
            structures = diag_layer.diag_data_dictionary_spec.structures
            self._structure = structures[self.structure_snref]

        if self.env_data_desc_snref is not None:
            env_data_descs = diag_layer.diag_data_dictionary_spec.env_data_descs
            self._env_data_desc = env_data_descs[self.env_data_desc_snref]

    def __repr__(self) -> str:
        return f"EndOfPduField(short_name='{self.short_name}', ref='{self.structure.odx_id}')"

    def __str__(self):
        return "\n".join(
            [f"EndOfPduField(short_name='{self.short_name}', ref='{self.structure.odx_id}')"] +
            [" " + str(self.structure).replace("\n", "\n ")])
